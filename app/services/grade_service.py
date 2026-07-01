from django.db import transaction

from app.models import CargaHoraria, Disciplina, Turma
from app.repositories import GradeRepository
from app.services.simulacao_service import SimulacaoService


class GradeService:
    def __init__(self, grade_repository=None, simulacao_service=None):
        self.grade_repository = grade_repository or GradeRepository()
        self.simulacao_service = simulacao_service or SimulacaoService()

    def criar_grade(self, *, periodo, aluno, turmas=None):
        return self.grade_repository.create(
            periodo=periodo,
            aluno=aluno,
            turmas=turmas,
        )

    def obter_grade(self, grade_id):
        return self.grade_repository.get(grade_id)

    def listar_grades(self):
        return self.grade_repository.list()

    def listar_do_aluno(self, aluno):
        return (
            self.grade_repository.list()
            .filter(aluno=aluno)
            .order_by("-periodo")
        )

    def atualizar_grade(self, grade_id, *, periodo=None, aluno=None, turmas=None):
        campos = {}
        if periodo is not None:
            campos["periodo"] = periodo
        if aluno is not None:
            campos["aluno"] = aluno
        return self.grade_repository.update(grade_id, turmas=turmas, **campos)

    def excluir_grade(self, grade_id):
        return self.grade_repository.delete(grade_id)

    @transaction.atomic
    def criar_grade_do_aluno(self, *, aluno, periodo, selecoes):
        grade = self.grade_repository.create(periodo=periodo, aluno=aluno, turmas=[])

        turmas_criadas = []
        for i, sel in enumerate(selecoes, start=1):
            disciplina = Disciplina.objects.get(id=sel["disciplina_id"])
            cargas = list(
                CargaHoraria.objects.filter(id__in=sel.get("carga_horaria_ids", []))
            )
            turma = Turma(
                codigo=f"T{i:02d}",
                grade=grade,
                disciplina=disciplina,
            )
            turma.full_clean()
            turma.save()
            if cargas:
                turma.carga_horarias.set(cargas)
            turmas_criadas.append(turma)

        self.simulacao_service.detectar_conflito_horario(turmas=turmas_criadas)
        return self.grade_repository.get(grade.id)
