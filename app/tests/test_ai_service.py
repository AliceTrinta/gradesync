"""
Testes unitarios do AIService (integracao com Google Gemini).

Todos os testes MOCKAM o cliente Gemini — nunca batem na rede. O teste
de integracao real (opt-in) vive em test_ai_integration.py e so roda
com AI_API_KEY setada.

Padrao usado:
- `AIService(client=Mock(), api_key="fake", ...)` -> pula o _get_client()
  e usa o mock direto em _chamar_gemini.
- Cache Django e limpado no setUp para nao vazar entre testes.
"""
import json
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from types import SimpleNamespace

from app.exceptions import (
    AIProviderError,
    AIQuotaExceededError,
    AIRespostaInvalidaError,
    AITimeoutError,
)
from app.services import AIService
from app.services.ai_service import (
    HORA_MAX,
    HORA_MIN,
    SYSTEM_DUVIDAS,
    SYSTEM_ROTEIRO,
)


def _mock_client_com_texto(texto):
    """Devolve um Mock que responde com client.models.generate_content().text = texto."""
    client = Mock()
    resposta = SimpleNamespace(text=texto)
    client.models.generate_content.return_value = resposta
    return client


def _mock_client_que_levanta(exc):
    client = Mock()
    client.models.generate_content.side_effect = exc
    return client


class AIServiceRoteiroTests(TestCase):
    """AIService.sugerir_roteiro: parseia JSON, valida, cacheia."""

    def setUp(self):
        cache.clear()
        self.aluno = SimpleNamespace(user=SimpleNamespace(first_name="Ana"))
        self.grade = SimpleNamespace(periodo="2026.1")
        self.blocos_livres = [
            ("seg", "14:00", "16:00"),
            ("qua", "10:00", "12:00"),
        ]
        self.disciplinas_meta = [
            {
                "codigo": "CC-201",
                "nome": "Estruturas de Dados",
                "carga_horaria": 60,
                "horarios_de_aula": [("ter", "08:00", "10:00")],
                "pre_requisitos": ["CC-101"],
            },
        ]

    def _service_com(self, texto):
        return AIService(
            client=_mock_client_com_texto(texto), api_key="fake"
        )

    def test_resposta_json_valida_e_parseada(self):
        resposta_json = json.dumps({
            "slots": [
                {"dia": "seg", "hora_inicio": "14:00", "hora_final": "16:00",
                 "titulo": "Estudar CC-201", "cor": "blue"}
            ],
            "raciocinio": "aproveitei o bloco de segunda",
        })
        service = self._service_com(resposta_json)

        resultado = service.sugerir_roteiro(
            aluno=self.aluno, grade=self.grade,
            blocos_livres=self.blocos_livres,
            disciplinas_meta=self.disciplinas_meta,
        )

        self.assertIsInstance(resultado, dict)
        self.assertEqual(len(resultado["slots"]), 1)
        self.assertEqual(resultado["slots"][0]["dia"], "seg")
        self.assertEqual(resultado["raciocinio"], "aproveitei o bloco de segunda")

    def test_resposta_nao_json_levanta_resposta_invalida(self):
        service = self._service_com("nao sou json de jeito nenhum")

        with self.assertRaises(AIRespostaInvalidaError):
            service.sugerir_roteiro(
                aluno=self.aluno, grade=self.grade,
                blocos_livres=self.blocos_livres,
                disciplinas_meta=self.disciplinas_meta,
            )

    def test_resposta_json_sem_chave_slots_levanta_resposta_invalida(self):
        service = self._service_com(json.dumps({"raciocinio": "opa"}))

        with self.assertRaises(AIRespostaInvalidaError) as ctx:
            service.sugerir_roteiro(
                aluno=self.aluno, grade=self.grade,
                blocos_livres=self.blocos_livres,
                disciplinas_meta=self.disciplinas_meta,
            )
        self.assertIn("slots", str(ctx.exception))

    def test_sem_api_key_levanta_provider_error_sem_chamar_sdk(self):
        client = Mock()
        service = AIService(client=client, api_key="")

        with self.assertRaises(AIProviderError):
            service.sugerir_roteiro(
                aluno=self.aluno, grade=self.grade,
                blocos_livres=self.blocos_livres,
                disciplinas_meta=self.disciplinas_meta,
            )
        client.models.generate_content.assert_not_called()

    def test_cache_hit_nao_chama_sdk_uma_segunda_vez(self):
        resposta_json = json.dumps({
            "slots": [{"dia": "seg", "hora_inicio": "14:00",
                       "hora_final": "16:00", "titulo": "X", "cor": "blue"}],
            "raciocinio": "-",
        })
        client = _mock_client_com_texto(resposta_json)
        service = AIService(client=client, api_key="fake")

        service.sugerir_roteiro(
            aluno=self.aluno, grade=self.grade,
            blocos_livres=self.blocos_livres,
            disciplinas_meta=self.disciplinas_meta,
        )
        service.sugerir_roteiro(
            aluno=self.aluno, grade=self.grade,
            blocos_livres=self.blocos_livres,
            disciplinas_meta=self.disciplinas_meta,
        )
        self.assertEqual(client.models.generate_content.call_count, 1)


class AIServiceChamarGeminiTests(TestCase):
    """AIService._chamar_gemini: traducao de erros do SDK."""

    def setUp(self):
        cache.clear()

    def test_timeout_do_sdk_vira_ai_timeout_error(self):
        service = AIService(
            client=_mock_client_que_levanta(TimeoutError("estourou")),
            api_key="fake",
        )
        with self.assertRaises(AITimeoutError):
            service._chamar_gemini("qualquer", esperar_json=False, tag="t")

    def test_erro_com_palavra_quota_vira_quota_exceeded(self):
        service = AIService(
            client=_mock_client_que_levanta(RuntimeError("429 quota exceeded")),
            api_key="fake",
        )
        with self.assertRaises(AIQuotaExceededError):
            service._chamar_gemini("qualquer", esperar_json=False, tag="t")

    def test_erro_com_palavra_rate_vira_quota_exceeded(self):
        service = AIService(
            client=_mock_client_que_levanta(RuntimeError("rate limit hit")),
            api_key="fake",
        )
        with self.assertRaises(AIQuotaExceededError):
            service._chamar_gemini("qualquer", esperar_json=False, tag="t")

    def test_erro_com_palavra_deadline_vira_ai_timeout(self):
        service = AIService(
            client=_mock_client_que_levanta(RuntimeError("deadline exceeded")),
            api_key="fake",
        )
        with self.assertRaises(AITimeoutError):
            service._chamar_gemini("qualquer", esperar_json=False, tag="t")

    def test_erro_generico_vira_provider_error(self):
        service = AIService(
            client=_mock_client_que_levanta(RuntimeError("boom desconhecido")),
            api_key="fake",
        )
        with self.assertRaises(AIProviderError) as ctx:
            service._chamar_gemini("qualquer", esperar_json=False, tag="tag-x")
        self.assertIn("tag-x", str(ctx.exception))

    def test_resposta_com_text_vazio_vira_resposta_invalida(self):
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(text="")
        service = AIService(client=client, api_key="fake")
        with self.assertRaises(AIRespostaInvalidaError):
            service._chamar_gemini("qualquer", esperar_json=False, tag="t")

    def test_esperar_json_seta_response_mime_type(self):
        client = _mock_client_com_texto('{"ok": true}')
        service = AIService(client=client, api_key="fake")
        service._chamar_gemini("qualquer", esperar_json=True, tag="t")

        _, kwargs = client.models.generate_content.call_args
        cfg = kwargs.get("config")
        self.assertEqual(cfg.response_mime_type, "application/json")

    def test_esperar_json_false_nao_seta_response_mime_type(self):
        client = _mock_client_com_texto("texto livre")
        service = AIService(client=client, api_key="fake")
        service._chamar_gemini("qualquer", esperar_json=False, tag="t")

        _, kwargs = client.models.generate_content.call_args
        cfg = kwargs.get("config")
        self.assertIsNone(cfg.response_mime_type)


class AIServiceResponderDuvidaTests(TestCase):
    """AIService.responder_duvida: texto livre + contexto sem PII."""

    def setUp(self):
        cache.clear()
        self.aluno = SimpleNamespace(user=SimpleNamespace(first_name="Bruno"))

    def test_resposta_e_string_com_texto_trim(self):
        client = _mock_client_com_texto("  Ola! Aqui esta a resposta.  ")
        service = AIService(client=client, api_key="fake")

        texto = service.responder_duvida(
            aluno=self.aluno, pergunta="Como criar uma grade?",
        )
        self.assertEqual(texto, "Ola! Aqui esta a resposta.")

    def test_cache_hit_na_duvida_nao_chama_sdk_duas_vezes(self):
        client = _mock_client_com_texto("resposta cacheada")
        service = AIService(client=client, api_key="fake")
        service.responder_duvida(aluno=self.aluno, pergunta="P")
        service.responder_duvida(aluno=self.aluno, pergunta="P")
        self.assertEqual(client.models.generate_content.call_count, 1)

    def test_use_cache_false_ignora_cache_e_chama_sdk_todas_as_vezes(self):
        client = _mock_client_com_texto("resposta")
        service = AIService(client=client, api_key="fake")
        service.responder_duvida(aluno=self.aluno, pergunta="P", use_cache=False)
        service.responder_duvida(aluno=self.aluno, pergunta="P", use_cache=False)
        self.assertEqual(client.models.generate_content.call_count, 2)


class AIServicePromptSemPIITests(TestCase):
    """Verifica que o prompt de duvidas NAO vaza matricula nem email."""

    def test_contexto_duvidas_nao_inclui_matricula_nem_email(self):
        aluno = SimpleNamespace(
            matricula="2026999-SECRETA",
            email="ana.secreto@example.com",
            user=SimpleNamespace(
                first_name="Ana",
                last_name="Silva",
                email="ana.secreto@example.com",
                username="ana_login_secreto",
            ),
        )
        service = AIService(api_key="fake")

        contexto = service._montar_contexto_duvidas(
            aluno=aluno, grade=None, roteiro=None,
            prefs_conta=None, tela_atual="/duvidas/",
        )
        self.assertNotIn("2026999", contexto)
        self.assertNotIn("SECRETA", contexto)
        self.assertNotIn("ana.secreto@example.com", contexto)
        self.assertNotIn("ana_login_secreto", contexto)
        self.assertIn("Ana", contexto)

    def test_contexto_duvidas_reporta_nao_tem_grade_quando_None(self):
        aluno = SimpleNamespace(user=SimpleNamespace(first_name="Ana"))
        service = AIService(api_key="fake")

        contexto = service._montar_contexto_duvidas(
            aluno=aluno, grade=None, roteiro=None,
            prefs_conta=None, tela_atual="",
        )
        self.assertIn("NAO", contexto)
        self.assertIn("/grades/nova/", contexto)

    def test_contexto_duvidas_reporta_tem_grade_com_disciplinas(self):
        aluno = SimpleNamespace(user=SimpleNamespace(first_name="Ana"))
        turma = SimpleNamespace(disciplina=SimpleNamespace(codigo="CC-201"))
        grade = SimpleNamespace(
            periodo="2026.1",
            turmas=SimpleNamespace(
                select_related=lambda *_: SimpleNamespace(all=lambda: [turma]),
            ),
        )
        service = AIService(api_key="fake")

        contexto = service._montar_contexto_duvidas(
            aluno=aluno, grade=grade, roteiro=None,
            prefs_conta=None, tela_atual="",
        )
        self.assertIn("SIM", contexto)
        self.assertIn("2026.1", contexto)
        self.assertIn("CC-201", contexto)

    def test_contexto_duvidas_reporta_tem_roteiro_com_slots(self):
        aluno = SimpleNamespace(user=SimpleNamespace(first_name="Ana"))
        roteiro = SimpleNamespace(slots=[
            {"dia": "seg", "hora_inicio": "14:00", "hora_final": "16:00"},
            {"dia": "qua", "hora_inicio": "10:00", "hora_final": "12:00"},
        ])
        service = AIService(api_key="fake")

        contexto = service._montar_contexto_duvidas(
            aluno=aluno, grade=None, roteiro=roteiro,
            prefs_conta=None, tela_atual="",
        )
        self.assertIn("2 blocos", contexto)


class AIServicePromptRoteiroTests(TestCase):
    """Verifica que o prompt do roteiro inclui blocos livres + disciplinas."""

    def test_prompt_roteiro_inclui_todos_os_blocos_livres(self):
        aluno = SimpleNamespace(user=SimpleNamespace(first_name="Carlos"))
        grade = SimpleNamespace(periodo="2026.2")
        blocos_livres = [
            ("seg", "14:00", "16:00"),
            ("qua", "10:00", "12:00"),
            ("sex", "16:00", "18:00"),
        ]
        disciplinas_meta = [
            {"codigo": "CC-101", "nome": "Intro Prog",
             "carga_horaria": 60,
             "horarios_de_aula": [("ter", "08:00", "10:00")],
             "pre_requisitos": []},
        ]
        service = AIService(api_key="fake")

        prompt = service._montar_prompt_roteiro(
            aluno=aluno, grade=grade,
            blocos_livres=blocos_livres,
            disciplinas_meta=disciplinas_meta,
        )
        self.assertIn("Carlos", prompt)
        self.assertIn("2026.2", prompt)
        self.assertIn("CC-101", prompt)
        self.assertIn("Intro Prog", prompt)
        for dia, ini, fim in blocos_livres:
            self.assertIn(f"{dia} {ini}-{fim}", prompt)

    def test_prompt_roteiro_menciona_faixa_horaria_permitida(self):
        aluno = SimpleNamespace(user=SimpleNamespace(first_name="X"))
        grade = SimpleNamespace(periodo="2026.1")
        service = AIService(api_key="fake")
        prompt = service._montar_prompt_roteiro(
            aluno=aluno, grade=grade,
            blocos_livres=[], disciplinas_meta=[],
        )
        self.assertIn(HORA_MIN, prompt)
        self.assertIn(HORA_MAX, prompt)


class AIServiceSystemPromptTests(TestCase):
    """Verifica que os system prompts contem as regras criticas."""

    def test_system_roteiro_menciona_regras_criticas(self):
        self.assertIn("06:00", SYSTEM_ROTEIRO)
        self.assertIn("22:00", SYSTEM_ROTEIRO)
        self.assertIn("NUNCA", SYSTEM_ROTEIRO)
        self.assertIn("JSON", SYSTEM_ROTEIRO)
        for cor in ("blue", "green", "purple", "red", "orange", "yellow"):
            self.assertIn(cor, SYSTEM_ROTEIRO)

    def test_system_duvidas_menciona_regras_de_tom(self):
        self.assertIn("portugues", SYSTEM_DUVIDAS.lower())
        self.assertIn("gradesync", SYSTEM_DUVIDAS.lower())
        self.assertIn("grade", SYSTEM_DUVIDAS.lower())


class AIServiceGetClientTests(TestCase):
    """AIService._get_client: importe lazy do SDK."""

    def test_sem_biblioteca_google_generativeai_vira_provider_error(self):
        """Se o import do google.genai falhar, levanta AIProviderError."""
        import sys

        service = AIService(api_key="fake")

        with patch.dict(sys.modules, {"google.genai": None, "google": None}):
            with self.assertRaises(AIProviderError):
                service._get_client()

    def test_cliente_injetado_no_construtor_e_devolvido_como_esta(self):
        client = Mock()
        service = AIService(client=client, api_key="fake")
        self.assertIs(service._get_client(), client)


@override_settings(AI_API_KEY="fake-de-override")
class AIServiceDefaultsFromSettingsTests(TestCase):
    """AIService le AI_API_KEY / AI_MODEL / AI_TIMEOUT_SECONDS de settings."""

    def test_construtor_usa_settings_quando_argumentos_sao_None(self):
        service = AIService()
        self.assertEqual(service.api_key, "fake-de-override")
        self.assertTrue(service.model_name)
        self.assertTrue(service.timeout)
