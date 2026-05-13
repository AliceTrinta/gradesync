from app.repositories import TurmaRepository


class TurmaService:
    def __init__(self, turma_repository=None):
        self.turma_repository = turma_repository or TurmaRepository()

    def criar_turma(self, *, codigo, grade, disciplina, carga_horarias=None):
        return self.turma_repository.create(
            codigo=codigo,
            grade=grade,
            disciplina=disciplina,
            carga_horarias=carga_horarias,
        )

    def obter_turma(self, turma_id):
        return self.turma_repository.get(turma_id)

    def listar_turmas(self):
        return self.turma_repository.list()

    def atualizar_turma(
        self,
        turma_id,
        *,
        codigo=None,
        grade=None,
        disciplina=None,
        carga_horarias=None,
    ):
        campos = {}
        if codigo is not None:
            campos["codigo"] = codigo
        if grade is not None:
            campos["grade"] = grade
        if disciplina is not None:
            campos["disciplina"] = disciplina
        return self.turma_repository.update(
            turma_id,
            carga_horarias=carga_horarias,
            **campos,
        )

    def excluir_turma(self, turma_id):
        return self.turma_repository.delete(turma_id)
