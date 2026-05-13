from app.repositories import GradeRepository


class GradeService:
    def __init__(self, grade_repository=None):
        self.grade_repository = grade_repository or GradeRepository()

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

    def atualizar_grade(self, grade_id, *, periodo=None, aluno=None, turmas=None):
        campos = {}
        if periodo is not None:
            campos["periodo"] = periodo
        if aluno is not None:
            campos["aluno"] = aluno

        return self.grade_repository.update(grade_id, turmas=turmas, **campos)

    def excluir_grade(self, grade_id):
        return self.grade_repository.delete(grade_id)
