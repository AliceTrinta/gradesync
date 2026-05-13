from app.repositories import ProfessorRepository


class ProfessorService:
    def __init__(self, professor_repository=None):
        self.professor_repository = professor_repository or ProfessorRepository()

    def criar_professor(self, *, nome, avaliacao):
        return self.professor_repository.create(nome=nome, avaliacao=avaliacao)

    def obter_professor(self, professor_id):
        return self.professor_repository.get(professor_id)

    def listar_professores(self):
        return self.professor_repository.list()

    def atualizar_professor(self, professor_id, *, nome=None, avaliacao=None):
        campos = {}
        if nome is not None:
            campos["nome"] = nome
        if avaliacao is not None:
            campos["avaliacao"] = avaliacao
        return self.professor_repository.update(professor_id, **campos)
