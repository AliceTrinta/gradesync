from app.repositories import AvaliacaoRepository


class AvaliacaoService:
    def __init__(self, avaliacao_repository=None):
        self.avaliacao_repository = avaliacao_repository or AvaliacaoRepository()

    def criar_avaliacao(self, *, ano, semestre, nota, aluno, professor, disciplina):
        return self.avaliacao_repository.create(
            ano=ano,
            semestre=semestre,
            nota=nota,
            aluno=aluno,
            professor=professor,
            disciplina=disciplina,
        )

    def obter_avaliacao(self, avaliacao_id):
        return self.avaliacao_repository.get(avaliacao_id)

    def listar_avaliacoes(self):
        return self.avaliacao_repository.list()

    def atualizar_avaliacao(
        self,
        avaliacao_id,
        *,
        ano=None,
        semestre=None,
        nota=None,
        aluno=None,
        professor=None,
        disciplina=None,
    ):
        campos = {}
        if ano is not None:
            campos["ano"] = ano
        if semestre is not None:
            campos["semestre"] = semestre
        if nota is not None:
            campos["nota"] = nota
        if aluno is not None:
            campos["aluno"] = aluno
        if professor is not None:
            campos["professor"] = professor
        if disciplina is not None:
            campos["disciplina"] = disciplina
        return self.avaliacao_repository.update(avaliacao_id, **campos)

    def excluir_avaliacao(self, avaliacao_id):
        return self.avaliacao_repository.delete(avaliacao_id)
