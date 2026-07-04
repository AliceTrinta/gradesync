import hashlib
import json

from django.conf import settings
from django.core.cache import cache

from app.exceptions import (
    AIProviderError,
    AIQuotaExceededError,
    AIRespostaInvalidaError,
    AITimeoutError,
)


CACHE_TTL_ROTEIRO = 60 * 60
CACHE_TTL_DUVIDA = 60 * 30

HORA_MIN = "06:00"
HORA_MAX = "22:00"


SYSTEM_ROTEIRO = """Voce e o gerador de roteiros de estudo do GradeSync, um \
sistema academico brasileiro. Sua tarefa e criar um roteiro de estudo \
semanal para UM aluno especifico, respeitando estritamente a grade de \
aulas dele.

REGRAS OBRIGATORIAS (nao violar sob nenhuma hipotese):
1. NUNCA agende estudo em horario que colida com aula da grade do aluno.
   Use apenas os blocos livres fornecidos.
2. Horarios PERMITIDOS: entre 06:00 e 22:00. NUNCA agende antes das 06:00
   nem depois das 22:00 (evitar madrugada / noite tardia).
3. Cada bloco deve ter 1 hora OU 2 horas de duracao (nunca menos, nunca
   mais).
4. Maximo 3 blocos por dia. Maximo 12 blocos na semana toda.
5. Maximo 2 blocos consecutivos da mesma disciplina no mesmo dia.
6. Distribua a carga proporcionalmente: disciplinas com maior
   carga_horaria devem ter MAIS blocos que as com menor.
7. Prefira dias em que o aluno tem menos aulas (mais espaco mental).
8. Diversifique disciplinas ao longo da semana.
9. Titulos dos slots devem estar em portugues (ex.: "Estudar CC-201 -
   Estruturas de Dados"), maximo 60 caracteres.

FORMATO DE RESPOSTA (JSON puro, sem markdown, sem ```, sem texto extra):
{
  "slots": [
    {"dia": "seg", "hora_inicio": "14:00", "hora_final": "16:00",
     "titulo": "Estudar CC-201 - Estruturas de Dados", "cor": "blue"}
  ],
  "raciocinio": "Uma frase curta em PT-BR explicando a logica."
}

Valores permitidos:
- dia: seg | ter | qua | qui | sex | sab | dom
- hora_inicio / hora_final: HH:MM (24h, zero-padded)
- cor: blue | green | purple | red | orange | yellow"""


SYSTEM_DUVIDAS = """Voce e o assistente virtual do GradeSync, um sistema \
academico web brasileiro que ajuda alunos de graduacao a:
- Montar sua grade do semestre (wizard em /grades/nova/)
- Gerar roteiros de estudo semanais (/roteiro/)
- Editar blocos do roteiro (adicionar, editar, remover slots)
- Consultar notificacoes, ajustar acessibilidade, tema e idioma

REGRAS DE RESPOSTA:
1. Responda SEMPRE em portugues do Brasil, tom amigavel e direto.
2. Maximo 4 paragrafos curtos. Use bullets com "\u2022" quando fizer
   sentido listar coisas.
3. Emojis discretos no inicio da resposta sao bem-vindos:
   \U0001F4C5 grade, \U0001F4D6 roteiro, \u2699\ufe0f config, \u267f acessibilidade,
   \U0001F512 privacidade, \U0001F511 senha, \U0001F514 notificacoes, \u2705 confirmacao.
4. NUNCA invente funcionalidades. Se o aluno pedir algo que o sistema
   nao faz, diga isso educadamente e sugira uma alternativa entre as
   areas listadas acima.
5. Se a pergunta for sobre a grade OU o roteiro do aluno, use o
   contexto fornecido para responder de forma personalizada.
6. Fluxo padrao do produto: aluno cria grade em /grades/nova/ (escolhe
   curso, disciplinas e horarios; sistema detecta conflitos), depois
   vai em Roteiro e gera roteiro de estudo (deterministico ou via IA);
   o editor de blocos permite ajustes manuais.
7. Regra fixa que voce nao pode contornar: ROTEIRO EXIGE GRADE
   cadastrada. Se o aluno nao tem grade, oriente ele a criar primeiro."""


class AIService:
    """Adapter sobre google-generativeai. Injetavel via construtor."""

    def __init__(self, client=None, model=None, timeout=None, api_key=None):
        self.api_key = api_key if api_key is not None else settings.AI_API_KEY
        self.model_name = model or settings.AI_MODEL
        self.timeout = timeout or settings.AI_TIMEOUT_SECONDS
        self._client = client

    def sugerir_roteiro(self, *, aluno, grade, blocos_livres, disciplinas_meta,
                        use_cache=True):
        self._exigir_api_key()

        user_prompt = self._montar_prompt_roteiro(
            aluno=aluno,
            grade=grade,
            blocos_livres=blocos_livres,
            disciplinas_meta=disciplinas_meta,
        )
        full_prompt = SYSTEM_ROTEIRO + "\n\n---\n\n" + user_prompt

        chave_cache = self._chave_cache("roteiro", full_prompt)
        if use_cache:
            cached = cache.get(chave_cache)
            if cached is not None:
                return cached

        texto = self._chamar_gemini(
            full_prompt, esperar_json=True, tag="sugerir_roteiro"
        )
        try:
            resultado = json.loads(texto)
        except (json.JSONDecodeError, TypeError) as exc:
            preview = (texto or "")[:200].replace("\n", " ")
            raise AIRespostaInvalidaError(
                f"nao foi JSON parseavel: {exc} | preview={preview!r}"
            ) from exc

        if not isinstance(resultado, dict) or "slots" not in resultado:
            raise AIRespostaInvalidaError(
                "resposta sem chave 'slots' no nivel raiz"
            )

        if use_cache:
            cache.set(chave_cache, resultado, CACHE_TTL_ROTEIRO)

        return resultado

    def responder_duvida(self, *, aluno, pergunta, tela_atual="",
                         grade=None, roteiro=None, prefs_conta=None,
                         use_cache=True):
        self._exigir_api_key()

        contexto = self._montar_contexto_duvidas(
            aluno=aluno,
            grade=grade,
            roteiro=roteiro,
            prefs_conta=prefs_conta,
            tela_atual=tela_atual,
        )
        user_prompt = f"{contexto}\n\nPERGUNTA DO ALUNO:\n{pergunta.strip()}"
        full_prompt = SYSTEM_DUVIDAS + "\n\n---\n\n" + user_prompt

        chave_cache = self._chave_cache("duvida", full_prompt)
        if use_cache:
            cached = cache.get(chave_cache)
            if cached is not None:
                return cached

        texto = self._chamar_gemini(
            full_prompt, esperar_json=False, tag="responder_duvida"
        )
        if use_cache:
            cache.set(chave_cache, texto, CACHE_TTL_DUVIDA)
        return texto

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise AIProviderError(
                "google-genai nao instalado. "
                "Rode: pip install -r requirements.txt"
            ) from exc

        self._client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(timeout=self.timeout * 1000),
        )
        return self._client

    def _chamar_gemini(self, prompt, *, esperar_json, tag):
        cliente = self._get_client()

        try:
            from google.genai import types as genai_types
        except ImportError as exc:
            raise AIProviderError(
                "google-genai nao instalado. "
                "Rode: pip install -r requirements.txt"
            ) from exc

        config_kwargs = {
            "max_output_tokens": settings.AI_MAX_TOKENS,
            "temperature": 0.2 if esperar_json else 0.7,
        }
        if esperar_json:
            config_kwargs["response_mime_type"] = "application/json"
            if "flash" in (self.model_name or "").lower():
                config_kwargs["thinking_config"] = genai_types.ThinkingConfig(
                    thinking_budget=0
                )

        try:
            resposta = cliente.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(**config_kwargs),
            )
        except TimeoutError as exc:
            raise AITimeoutError(
                provedor=settings.AI_PROVIDER, segundos=self.timeout
            ) from exc
        except Exception as exc:
            msg = str(exc).lower()
            if "quota" in msg or "rate" in msg or "429" in msg:
                raise AIQuotaExceededError(
                    provedor=settings.AI_PROVIDER, motivo=str(exc)
                ) from exc
            if "timeout" in msg or "deadline" in msg:
                raise AITimeoutError(
                    provedor=settings.AI_PROVIDER, segundos=self.timeout
                ) from exc
            raise AIProviderError(
                f"{tag}: falha ao chamar {settings.AI_PROVIDER}: {exc}"
            ) from exc

        texto = getattr(resposta, "text", None)
        if not texto:
            raise AIRespostaInvalidaError("resposta vazia da IA")
        return texto.strip()

    def _exigir_api_key(self):
        if not self.api_key:
            raise AIProviderError(
                "AI_API_KEY nao configurada. "
                "Defina no .env para habilitar a IA."
            )

    def _chave_cache(self, prefixo, prompt):
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return f"ai:{prefixo}:{self.model_name}:{digest}"

    def _montar_prompt_roteiro(self, *, aluno, grade, blocos_livres,
                               disciplinas_meta):
        nome = getattr(getattr(aluno, "user", None), "first_name", "") or "Aluno"

        linhas = ["CONTEXTO DO ALUNO:", f"- Nome: {nome}"]
        if getattr(grade, "periodo", None):
            linhas.append(f"- Periodo letivo: {grade.periodo}")
        linhas.append("")
        linhas.append(f"GRADE DO SEMESTRE ({len(disciplinas_meta)} disciplinas):")
        for d in disciplinas_meta:
            linhas.append(
                f"- {d['codigo']} - {d['nome']} "
                f"({d.get('carga_horaria', 0)}h/sem)"
            )
            horarios = d.get("horarios_de_aula", [])
            if horarios:
                linhas.append("  Horarios de aula:")
                for dia, ini, fim in horarios:
                    linhas.append(f"    - {dia} {ini}-{fim}")
            pre = d.get("pre_requisitos", [])
            if pre:
                linhas.append(f"  Pre-requisitos: {', '.join(pre)}")

        linhas.append("")
        linhas.append(
            f"BLOCOS LIVRES NA SEMANA "
            f"(horarios SEM aula, entre {HORA_MIN} e {HORA_MAX}, "
            f"voce DEVE escolher entre estes):"
        )
        for dia, ini, fim in blocos_livres:
            linhas.append(f"- {dia} {ini}-{fim}")

        linhas.append("")
        linhas.append(
            "Gere o roteiro em JSON conforme o schema instruido no "
            "system prompt."
        )
        return "\n".join(linhas)

    def _montar_contexto_duvidas(self, *, aluno, grade, roteiro,
                                 prefs_conta, tela_atual):
        linhas = ["CONTEXTO DO ALUNO ATUAL:"]

        nome = getattr(getattr(aluno, "user", None), "first_name", "") or "Aluno"
        linhas.append(f"- Nome: {nome}")

        if grade is not None:
            turmas = list(grade.turmas.select_related("disciplina").all())
            codigos = ", ".join(t.disciplina.codigo for t in turmas) or "nenhuma"
            linhas.append(
                f"- Tem grade cadastrada? SIM (periodo {grade.periodo}, "
                f"{len(turmas)} disciplinas: {codigos})"
            )
        else:
            linhas.append(
                "- Tem grade cadastrada? NAO (aluno precisa criar em "
                "/grades/nova/ antes de gerar roteiro)"
            )

        if roteiro is not None and getattr(roteiro, "slots", None):
            dias_com_estudo = {s.get("dia") for s in roteiro.slots if s.get("dia")}
            linhas.append(
                f"- Tem roteiro? SIM ({len(roteiro.slots)} blocos "
                f"distribuidos em {len(dias_com_estudo)} dias)"
            )
        else:
            linhas.append("- Tem roteiro? NAO")

        if prefs_conta is not None:
            linhas.append(
                f"- Preferencias: idioma={prefs_conta.idioma}, "
                f"tema={prefs_conta.tema}"
            )

        if tela_atual:
            linhas.append(f"- Tela atual (de onde perguntou): {tela_atual}")

        return "\n".join(linhas)
