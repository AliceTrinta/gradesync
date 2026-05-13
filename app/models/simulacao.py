import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Simulacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    periodo = models.CharField(max_length=16)
    aluno = models.ForeignKey(
        "app.Aluno",
        on_delete=models.CASCADE,
        related_name="simulacoes",
    )
    turmas = models.ManyToManyField(
        "app.Turma",
        blank=True,
        related_name="simulacoes",
    )

    class Meta:
        verbose_name = "simulacao"
        verbose_name_plural = "simulacoes"

    def clean(self):
        super().clean()
        self.periodo = (self.periodo or "").strip()
        if not self.periodo:
            raise ValidationError({"periodo": "O periodo nao pode ficar vazio."})

    def __str__(self):
        return f"{self.aluno} - {self.periodo}"
