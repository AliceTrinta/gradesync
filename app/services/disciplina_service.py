from app.repositories import DisciplinaRepository


class DisciplinaService:
    def __init__(self, disciplina_repository=None):
        self.disciplina_repository = disciplina_repository or DisciplinaRepository()

    def criar_disciplina(
        self,
        *,
        codigo,
        nome,
        taxa_de_reprovacao,
        pre_requisitos=None,
    ):
        return self.disciplina_repository.create(
            codigo=codigo,
            nome=nome,
            taxa_de_reprovacao=taxa_de_reprovacao,
            pre_requisitos=pre_requisitos,
        )

    def obter_disciplina(self, disciplina_id):
        return self.disciplina_repository.get(disciplina_id)

    def listar_disciplinas(self):
        return self.disciplina_repository.list()

    def atualizar_disciplina(
        self,
        disciplina_id,
        *,
        codigo=None,
        nome=None,
        taxa_de_reprovacao=None,
        pre_requisitos=None,
    ):
        campos = {}
        if codigo is not None:
            campos["codigo"] = codigo
        if nome is not None:
            campos["nome"] = nome
        if taxa_de_reprovacao is not None:
            campos["taxa_de_reprovacao"] = taxa_de_reprovacao
        return self.disciplina_repository.update(
            disciplina_id,
            pre_requisitos=pre_requisitos,
            **campos,
        )
