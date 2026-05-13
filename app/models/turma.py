import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Turma(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=32)
    grade = models.ForeignKey(
        "app.Grade",
        on_delete=models.CASCADE,
        related_name="turmas",
    )
    disciplina = models.ForeignKey(
        "app.Disciplina",
        on_delete=models.CASCADE,
        related_name="turmas",
    )
    carga_horarias = models.ManyToManyField(
        "app.CargaHoraria",
        blank=True,
        related_name="turmas",
    )

    class Meta:
        verbose_name = "turma"
        verbose_name_plural = "turmas"
        constraints = [
            models.UniqueConstraint(
                fields=["codigo", "grade", "disciplina"],
                name="unique_turma_por_grade_disciplina",
            )
        ]

    def clean(self):
        super().clean()
        self.codigo = (self.codigo or "").strip()
        if not self.codigo:
            raise ValidationError({"codigo": "O codigo nao pode ficar vazio."})

    def __str__(self):
        disciplina_codigo = getattr(self.disciplina, "codigo", self.disciplina_id)
        return f"{self.codigo} - {disciplina_codigo}"
