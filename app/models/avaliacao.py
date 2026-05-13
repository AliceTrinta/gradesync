import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Avaliacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ano = models.PositiveIntegerField(validators=[MinValueValidator(2000)])
    semestre = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)]
    )
    nota = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    aluno = models.ForeignKey(
        "app.Aluno",
        on_delete=models.PROTECT,
        related_name="avaliacoes",
    )
    professor = models.ForeignKey(
        "app.Professor",
        on_delete=models.PROTECT,
        related_name="avaliacoes_recebidas",
    )
    disciplina = models.ForeignKey(
        "app.Disciplina",
        on_delete=models.PROTECT,
        related_name="avaliacoes",
    )

    class Meta:
        verbose_name = "avaliacao"
        verbose_name_plural = "avaliacoes"

    def __str__(self):
        return f"{self.aluno} - {self.ano}/{self.semestre}: {self.nota}"
