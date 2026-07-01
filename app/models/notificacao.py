import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Notificacao(models.Model):
    TIPO_INFO = "info"
    TIPO_SUCESSO = "sucesso"
    TIPO_AVISO = "aviso"
    TIPO_ERRO = "erro"

    TIPOS = [
        (TIPO_INFO, "Informação"),
        (TIPO_SUCESSO, "Sucesso"),
        (TIPO_AVISO, "Aviso"),
        (TIPO_ERRO, "Erro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(
        "app.Aluno",
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    tipo = models.CharField(max_length=16, choices=TIPOS, default=TIPO_INFO)
    titulo = models.CharField(max_length=160)
    mensagem = models.TextField()
    link_acao = models.CharField(max_length=255, blank=True, default="")
    lida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "notificacao"
        verbose_name_plural = "notificacoes"
        ordering = ("-criada_em",)

    def clean(self):
        super().clean()
        self.titulo = (self.titulo or "").strip()
        self.mensagem = (self.mensagem or "").strip()
        if not self.titulo:
            raise ValidationError({"titulo": "O titulo nao pode ficar vazio."})
        if not self.mensagem:
            raise ValidationError({"mensagem": "A mensagem nao pode ficar vazia."})

    def __str__(self):
        marker = "" if self.lida else "* "
        return f"{marker}{self.titulo} ({self.aluno})"
