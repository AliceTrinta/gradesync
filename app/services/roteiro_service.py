import uuid
from datetime import datetime, time

from app.exceptions import (
    BlocoConflitaComGradeError,
    BlocoRoteiroInvalidoError,
    RoteiroSemGradeError,
)
from app.models import Turma
from app.repositories import RoteiroRepository


CORES = ["blue", "green", "purple", "amber", "red"]
DIAS_VALIDOS = {"seg", "ter", "qua", "qui", "sex", "sab", "dom"}

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
