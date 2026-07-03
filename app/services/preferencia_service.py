from app.repositories import (
    PreferenciaAcessibilidadeRepository,
    PreferenciaContaRepository,
)


class PreferenciaAcessibilidadeService:
    def __init__(self, repository=None):
        self.repository = repository or PreferenciaAcessibilidadeRepository()

    def obter_do_aluno(self, aluno):
        return self.repository.get_or_create_for(aluno)

    def atualizar(self, aluno, *, tamanho_fonte=None, alto_contraste=None,
                  reduzir_animacoes=None, sublinhar_links=None):
        campos = {}
        if tamanho_fonte is not None:
            campos["tamanho_fonte"] = tamanho_fonte
        if alto_contraste is not None:
            campos["alto_contraste"] = bool(alto_contraste)
        if reduzir_animacoes is not None:
            campos["reduzir_animacoes"] = bool(reduzir_animacoes)
        if sublinhar_links is not None:
            campos["sublinhar_links"] = bool(sublinhar_links)
        return self.repository.update_for(aluno, **campos)


class PreferenciaContaService:
    def __init__(self, repository=None):
        self.repository = repository or PreferenciaContaRepository()

    def obter_do_aluno(self, aluno):
        return self.repository.get_or_create_for(aluno)

    def atualizar(self, aluno, *, idioma=None, tema=None):
        campos = {}
        if idioma is not None:
            campos["idioma"] = idioma
        if tema is not None:
            campos["tema"] = tema
        return self.repository.update_for(aluno, **campos)
