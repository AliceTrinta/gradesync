import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Aluno(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="aluno",
    )
    matricula = models.CharField(max_length=32, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "aluno"
        verbose_name_plural = "alunos"

    def clean(self):
        super().clean()
        self.matricula = (self.matricula or "").strip()
        if not (self.matricula or "").strip():
            raise ValidationError({"matricula": "A matricula nao pode ficar vazia."})

    def __str__(self):
        if not self.ativo:
            return "(DESATIVADO)"
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.matricula})"
