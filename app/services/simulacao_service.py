from django.db import transaction

from app.exceptions import (
    ConflitoDeHorarioError,
    PrerequisitoNaoAtendidoError,
    SimulacaoIncompletaError,
)
from app.models import Avaliacao
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

    def validar_prerequisitos(self, *, aluno, disciplina, nota_minima_aprovacao=5):
        """Levanta PrerequisitoNaoAtendidoError se aluno nao passou nos pre-reqs.

        Considera aprovado quando existe pelo menos uma Avaliacao com
        nota >= nota_minima_aprovacao para o pre-requisito.
        """
        pre_reqs = list(disciplina.pre_requisitos.all())
        if not pre_reqs:
            return 

        aprovadas = set(
            Avaliacao.objects.filter(
                aluno=aluno,
                nota__gte=nota_minima_aprovacao,
            ).values_list("disciplina_id", flat=True)
        )

        faltantes = [pr for pr in pre_reqs if pr.id not in aprovadas]
        if faltantes:
            raise PrerequisitoNaoAtendidoError(disciplina, faltantes)

    def detectar_conflito_horario(self, *, turmas):
        """Verifica se ha sobreposicao de horario entre as turmas fornecidas.

        Levanta ConflitoDeHorarioError na primeira sobreposicao encontrada.
        """
        cargas_por_turma = []
        for turma in turmas:
            for carga in turma.carga_horarias.all():
                cargas_por_turma.append((turma, carga))

        for i in range(len(cargas_por_turma)):
            for j in range(i + 1, len(cargas_por_turma)):
                turma_a, carga_a = cargas_por_turma[i]
                turma_b, carga_b = cargas_por_turma[j]
                if turma_a.id == turma_b.id:
                    continue
                if carga_a.dia.strip().lower() != carga_b.dia.strip().lower():
                    continue
                if self._intervalos_se_sobrepoem(carga_a, carga_b):
                    raise ConflitoDeHorarioError(turma_a, turma_b, carga_a, carga_b)

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

    def _intervalos_se_sobrepoem(self, carga_a, carga_b):
        """True se dois intervalos de tempo se sobrepoem."""
        return (
            carga_a.hora_inicio < carga_b.hora_final
            and carga_b.hora_inicio < carga_a.hora_final
        )
