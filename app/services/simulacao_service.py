from django.db import transaction

from app.exceptions import SimulacaoIncompletaError
from app.repositories import GradeRepository, SimulacaoRepository


class SimulacaoService:
    def __init__(self, simulacao_repository=None, grade_repository=None):
        self.simulacao_repository = simulacao_repository or SimulacaoRepository()
        self.grade_repository = grade_repository or GradeRepository()

    def criar_simulacao(self, *, periodo, aluno, turmas=None):
        return self.simulacao_repository.create(
            periodo=periodo,
            aluno=aluno,
            turmas=turmas,
        )

    def obter_simulacao(self, simulacao_id):
        return self.simulacao_repository.get(simulacao_id)

    def listar_simulacoes(self):
        return self.simulacao_repository.list()

    def atualizar_simulacao(
        self,
        simulacao_id,
        *,
        periodo=None,
        aluno=None,
        turmas=None,
    ):
        campos = {}
        if periodo is not None:
            campos["periodo"] = periodo
        if aluno is not None:
            campos["aluno"] = aluno

        return self.simulacao_repository.update(simulacao_id, turmas=turmas, **campos)

    def excluir_simulacao(self, simulacao_id):
        return self.simulacao_repository.delete(simulacao_id)

    @transaction.atomic
    def confirmar_simulacao(self, simulacao_id):
        simulacao = self.simulacao_repository.get(simulacao_id)
        turmas = self._listar_turmas(simulacao)
        self._validar_simulacao_completa(simulacao, turmas)

        grade = self.grade_repository.create(
            periodo=simulacao.periodo.strip(),
            aluno=simulacao.aluno,
            turmas=turmas,
        )
        self.simulacao_repository.delete(simulacao.id)
        return grade

    def _validar_simulacao_completa(self, simulacao, turmas):
        erros = {}
        if not (getattr(simulacao, "periodo", "") or "").strip():
            erros["periodo"] = "Informe o periodo antes de confirmar a simulacao."
        if getattr(simulacao, "aluno", None) is None:
            erros["aluno"] = "Informe o aluno antes de confirmar a simulacao."
        if not turmas:
            erros["turmas"] = "Informe ao menos uma turma antes de confirmar a simulacao."

        if erros:
            raise SimulacaoIncompletaError(erros)

    def _listar_turmas(self, simulacao):
        turmas = getattr(simulacao, "turmas", [])
        if hasattr(turmas, "all"):
            return list(turmas.all())
        return list(turmas)
