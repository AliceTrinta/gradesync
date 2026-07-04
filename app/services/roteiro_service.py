import uuid
from datetime import datetime, time

from app.exceptions import (
    BlocoConflitaComGradeError,
    BlocoRoteiroInvalidoError,
    RoteiroSemGradeError,
)
from app.models import Turma
from app.repositories import RoteiroRepository


CORES = ["blue", "green", "purple", "red", "orange"]
DIAS_VALIDOS = {"seg", "ter", "qua", "qui", "sex", "sab", "dom"}
DIAS_ORDEM = ["seg", "ter", "qua", "qui", "sex", "sab"]

HORA_MIN_ESTUDO = "06:00"
HORA_MAX_ESTUDO = "22:00"

MIN_SLOTS_IA = 4

BLOCOS_ESTUDO = [
    ("seg", "08:00", "10:00"),
    ("qua", "08:00", "10:00"),
    ("sex", "08:00", "10:00"),
    ("seg", "14:00", "16:00"),
    ("qua", "14:00", "16:00"),
    ("sex", "14:00", "16:00"),
]


def _normalizar_dia(valor):
    return (valor or "").strip().lower()[:3]


def _normalizar_hora(valor):
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    texto = (valor or "").strip()
    if not texto:
        raise BlocoRoteiroInvalidoError("Horario e obrigatorio.")
    try:
        return datetime.strptime(texto, "%H:%M").strftime("%H:%M")
    except ValueError as exc:
        raise BlocoRoteiroInvalidoError(
            f"Horario invalido: '{texto}'. Use HH:MM."
        ) from exc


def _intervalos_se_sobrepoem(inicio_a, fim_a, inicio_b, fim_b):
    return inicio_a < fim_b and inicio_b < fim_a


class RoteiroService:
    def __init__(self, roteiro_repository=None):
        self.roteiro_repository = roteiro_repository or RoteiroRepository()

    def obter_do_aluno(self, aluno):
        return self.roteiro_repository.get_by_aluno(aluno)

    def salvar(self, *, aluno, slots, titulo=None, prompt_usado=""):
        return self.roteiro_repository.upsert_by_aluno(
            aluno=aluno,
            slots=slots,
            titulo=titulo,
            prompt_usado=prompt_usado,
        )

    def excluir_do_aluno(self, aluno):
        existente = self.roteiro_repository.get_by_aluno(aluno)
        if existente:
            self.roteiro_repository.delete(existente.id)
            return True
        return False

    def gerar_roteiro_padrao(self, *, aluno, grade, titulo=None):
        if grade is None:
            raise RoteiroSemGradeError()

        slots = self._montar_slots(grade)
        return self.salvar(
            aluno=aluno,
            slots=slots,
            titulo=titulo or f"Roteiro {grade.periodo}",
            prompt_usado=f"[gerado a partir da grade {grade.periodo}]",
        )

    def sugerir_roteiro_via_ia(self, *, aluno, grade, titulo=None,
                               ai_service=None):
        """Gera roteiro via IA. Se restar <MIN_SLOTS_IA slots validos
        apos filtragem, cai no gerador deterministico. AIProviderError
        propaga para a view decidir o fallback."""
        if grade is None:
            raise RoteiroSemGradeError()

        from app.services import AIService
        service_ia = ai_service or AIService()

        blocos_livres = self._blocos_livres_da_grade(grade)
        disciplinas_meta = self._disciplinas_meta_da_grade(grade)

        resultado = service_ia.sugerir_roteiro(
            aluno=aluno,
            grade=grade,
            blocos_livres=blocos_livres,
            disciplinas_meta=disciplinas_meta,
        )

        slots_brutos = resultado.get("slots") or []
        raciocinio = (resultado.get("raciocinio") or "").strip()

        slots_validos = []
        for bruto in slots_brutos:
            if not isinstance(bruto, dict):
                continue
            try:
                bloco = self._preparar_bloco(
                    dia=bruto.get("dia"),
                    hora_inicio=bruto.get("hora_inicio"),
                    hora_final=bruto.get("hora_final"),
                    titulo=bruto.get("titulo"),
                    cor=bruto.get("cor", "blue"),
                )
                self._garantir_sem_conflito_com_grade(aluno, bloco)
                self._garantir_dentro_da_faixa_permitida(bloco)
            except (BlocoRoteiroInvalidoError, BlocoConflitaComGradeError):
                continue
            slots_validos.append(bloco)

        if len(slots_validos) < MIN_SLOTS_IA:
            slots_finais = self._montar_slots(grade)
            prompt_usado = (
                f"[fallback deterministico apos IA devolver "
                f"{len(slots_validos)} slots validos (min={MIN_SLOTS_IA})]"
            )
        else:
            slots_finais = slots_validos
            prompt_usado = f"[IA] {raciocinio}" if raciocinio else "[IA]"

        return self.salvar(
            aluno=aluno,
            slots=slots_finais,
            titulo=titulo or f"Roteiro {grade.periodo}",
            prompt_usado=prompt_usado,
        )

    def _blocos_livres_da_grade(self, grade):
        h_min = int(HORA_MIN_ESTUDO.split(":", 1)[0])
        h_max = int(HORA_MAX_ESTUDO.split(":", 1)[0])

        ocupacao = {dia: set() for dia in DIAS_ORDEM}
        turmas = list(grade.turmas.select_related("disciplina").all())
        for turma in turmas:
            for carga in turma.carga_horarias.all():
                dia = _normalizar_dia(carga.dia)
                if dia not in ocupacao:
                    continue
                ini = int(carga.hora_inicio.strftime("%H"))
                fim = int(carga.hora_final.strftime("%H"))
                for h in range(ini, fim):
                    ocupacao[dia].add(h)

        blocos = []
        for dia in DIAS_ORDEM:
            hora = h_min
            while hora < h_max:
                if hora in ocupacao[dia]:
                    hora += 1
                    continue
                inicio = hora
                while hora < h_max and hora not in ocupacao[dia]:
                    hora += 1
                fim = hora
                if fim - inicio >= 1:
                    blocos.append(
                        (dia, f"{inicio:02d}:00", f"{fim:02d}:00")
                    )
        return blocos

    def _disciplinas_meta_da_grade(self, grade):
        turmas = list(grade.turmas.select_related("disciplina").all())
        meta = []
        for turma in turmas:
            disc = turma.disciplina
            horarios = [
                (
                    _normalizar_dia(c.dia),
                    c.hora_inicio.strftime("%H:%M"),
                    c.hora_final.strftime("%H:%M"),
                )
                for c in turma.carga_horarias.all()
            ]
            pre_reqs = [pr.codigo for pr in disc.pre_requisitos.all()]
            meta.append({
                "codigo": disc.codigo,
                "nome": disc.nome,
                "carga_horaria": getattr(disc, "carga_horaria", 0),
                "horarios_de_aula": horarios,
                "pre_requisitos": pre_reqs,
            })
        return meta

    def _garantir_dentro_da_faixa_permitida(self, bloco):
        if bloco["hora_inicio"] < HORA_MIN_ESTUDO:
            raise BlocoRoteiroInvalidoError(
                f"Bloco fora da faixa permitida (antes de {HORA_MIN_ESTUDO})."
            )
        if bloco["hora_final"] > HORA_MAX_ESTUDO:
            raise BlocoRoteiroInvalidoError(
                f"Bloco fora da faixa permitida (depois de {HORA_MAX_ESTUDO})."
            )

    def adicionar_bloco(self, aluno, *, dia, hora_inicio, hora_final, titulo, cor="blue"):
        bloco = self._preparar_bloco(
            dia=dia,
            hora_inicio=hora_inicio,
            hora_final=hora_final,
            titulo=titulo,
            cor=cor,
        )
        self._garantir_sem_conflito_com_grade(aluno, bloco)

        roteiro = self._obter_ou_criar_roteiro(aluno)
        slots = list(roteiro.slots or [])
        slots.append(bloco)
        return self.roteiro_repository.update(roteiro.id, slots=slots)

    def editar_bloco(self, aluno, *, bloco_id, dia, hora_inicio, hora_final, titulo, cor="blue"):
        roteiro = self._exigir_roteiro(aluno)
        slots = list(roteiro.slots or [])
        for i, slot in enumerate(slots):
            if slot.get("id") == bloco_id:
                break
        else:
            raise BlocoRoteiroInvalidoError("Bloco nao encontrado.")

        novo = self._preparar_bloco(
            dia=dia,
            hora_inicio=hora_inicio,
            hora_final=hora_final,
            titulo=titulo,
            cor=cor,
        )
        novo["id"] = bloco_id
        self._garantir_sem_conflito_com_grade(aluno, novo)

        slots[i] = novo
        return self.roteiro_repository.update(roteiro.id, slots=slots)

    def remover_bloco(self, aluno, *, bloco_id):
        roteiro = self._exigir_roteiro(aluno)
        slots = [s for s in (roteiro.slots or []) if s.get("id") != bloco_id]
        if len(slots) == len(roteiro.slots or []):
            raise BlocoRoteiroInvalidoError("Bloco nao encontrado.")
        return self.roteiro_repository.update(roteiro.id, slots=slots)

    def _preparar_bloco(self, *, dia, hora_inicio, hora_final, titulo, cor):
        dia_slug = _normalizar_dia(dia)
        if dia_slug not in DIAS_VALIDOS:
            raise BlocoRoteiroInvalidoError(f"Dia invalido: '{dia}'.")

        inicio = _normalizar_hora(hora_inicio)
        fim = _normalizar_hora(hora_final)
        if inicio >= fim:
            raise BlocoRoteiroInvalidoError(
                "Hora final deve ser posterior a hora inicial."
            )

        titulo_norm = (titulo or "").strip()
        if not titulo_norm:
            raise BlocoRoteiroInvalidoError("Titulo do bloco e obrigatorio.")

        return {
            "id": uuid.uuid4().hex,
            "dia": dia_slug,
            "hora_inicio": inicio,
            "hora_final": fim,
            "titulo": titulo_norm,
            "cor": cor if cor in CORES else "blue",
        }

    def _garantir_sem_conflito_com_grade(self, aluno, bloco):
        turmas = (
            Turma.objects.filter(grade__aluno=aluno)
            .select_related("disciplina")
            .prefetch_related("carga_horarias")
        )
        for turma in turmas:
            for carga in turma.carga_horarias.all():
                if _normalizar_dia(carga.dia) != bloco["dia"]:
                    continue
                inicio_carga = carga.hora_inicio.strftime("%H:%M")
                fim_carga = carga.hora_final.strftime("%H:%M")
                if _intervalos_se_sobrepoem(
                    bloco["hora_inicio"], bloco["hora_final"],
                    inicio_carga, fim_carga,
                ):
                    raise BlocoConflitaComGradeError(
                        dia=bloco["dia"],
                        hora_inicio=bloco["hora_inicio"],
                        hora_final=bloco["hora_final"],
                        disciplina_codigo=turma.disciplina.codigo,
                    )

    def _obter_ou_criar_roteiro(self, aluno):
        existente = self.roteiro_repository.get_by_aluno(aluno)
        if existente is not None:
            return existente
        return self.roteiro_repository.create(aluno=aluno, slots=[])

    def _exigir_roteiro(self, aluno):
        roteiro = self.roteiro_repository.get_by_aluno(aluno)
        if roteiro is None:
            raise BlocoRoteiroInvalidoError("Roteiro ainda nao foi gerado.")
        return roteiro

    def _montar_slots(self, grade):
        turmas = list(grade.turmas.select_related("disciplina").all())
        if not turmas:
            return []

        dias_ocupados = {
            _normalizar_dia(c.dia)
            for t in turmas
            for c in t.carga_horarias.all()
        }
        blocos = [b for b in BLOCOS_ESTUDO if b[0] not in dias_ocupados] or BLOCOS_ESTUDO

        return [
            {
                "id": uuid.uuid4().hex,
                "dia": dia,
                "hora_inicio": inicio,
                "hora_final": fim,
                "titulo": f"Estudar {turmas[i % len(turmas)].disciplina.codigo}",
                "cor": CORES[i % len(CORES)],
            }
            for i, (dia, inicio, fim) in enumerate(blocos)
        ]
