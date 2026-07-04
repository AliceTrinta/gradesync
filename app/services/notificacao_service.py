from app.models import Notificacao
from app.repositories import NotificacaoRepository


class NotificacaoService:
    """Regras de negocio para notificacoes do aluno."""

    def __init__(self, notificacao_repository=None):
        self.notificacao_repository = notificacao_repository or NotificacaoRepository()

    def criar(self, *, aluno, titulo, mensagem, tipo=Notificacao.TIPO_INFO, link_acao=""):
        return self.notificacao_repository.create(
            aluno=aluno,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            link_acao=link_acao,
        )

    def listar_do_aluno(self, aluno):
        return self.notificacao_repository.listar_por_aluno(aluno)

    def contar_nao_lidas(self, aluno):
        return self.notificacao_repository.contar_nao_lidas(aluno)

    def marcar_como_lida(self, notif_id, aluno):
        return self.notificacao_repository.marcar_como_lida(notif_id, aluno)

    def marcar_todas_como_lidas(self, aluno):
        return self.notificacao_repository.marcar_todas_como_lidas(aluno)

    def excluir(self, notif_id, aluno):
        return self.notificacao_repository.delete(notif_id, aluno)

    def info(self, aluno, titulo, mensagem, link_acao=""):
        return self.criar(aluno=aluno, titulo=titulo, mensagem=mensagem,
                          tipo=Notificacao.TIPO_INFO, link_acao=link_acao)

    def sucesso(self, aluno, titulo, mensagem, link_acao=""):
        return self.criar(aluno=aluno, titulo=titulo, mensagem=mensagem,
                          tipo=Notificacao.TIPO_SUCESSO, link_acao=link_acao)

    def aviso(self, aluno, titulo, mensagem, link_acao=""):
        return self.criar(aluno=aluno, titulo=titulo, mensagem=mensagem,
                          tipo=Notificacao.TIPO_AVISO, link_acao=link_acao)

    def erro(self, aluno, titulo, mensagem, link_acao=""):
        return self.criar(aluno=aluno, titulo=titulo, mensagem=mensagem,
                          tipo=Notificacao.TIPO_ERRO, link_acao=link_acao)
