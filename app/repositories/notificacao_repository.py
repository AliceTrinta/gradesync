from app.exceptions import EntidadeNaoEncontrada
from app.models import Notificacao


class NotificacaoRepository:
    def create(self, *, aluno, tipo, titulo, mensagem, link_acao=""):
        notif = Notificacao(
            aluno=aluno,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            link_acao=link_acao,
        )
        notif.full_clean()
        notif.save()
        return notif

    def get(self, notif_id):
        try:
            return Notificacao.objects.select_related("aluno").get(id=notif_id)
        except Notificacao.DoesNotExist as exc:
            raise EntidadeNaoEncontrada("Notificacao nao encontrada.") from exc

    def listar_por_aluno(self, aluno):
        return Notificacao.objects.filter(aluno=aluno)

    def contar_nao_lidas(self, aluno):
        return Notificacao.objects.filter(aluno=aluno, lida=False).count()

    def marcar_como_lida(self, notif_id, aluno):
        notif = self.get(notif_id)
        if notif.aluno_id != aluno.id:
            raise EntidadeNaoEncontrada("Notificacao nao encontrada.")
        if not notif.lida:
            notif.lida = True
            notif.save(update_fields=["lida"])
        return notif

    def marcar_todas_como_lidas(self, aluno):
        return Notificacao.objects.filter(aluno=aluno, lida=False).update(lida=True)

    def delete(self, notif_id, aluno):
        notif = self.get(notif_id)
        if notif.aluno_id != aluno.id:
            raise EntidadeNaoEncontrada("Notificacao nao encontrada.")
        notif.delete()
        return True
