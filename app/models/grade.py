import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Grade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    periodo = models.CharField(max_length=16)
    aluno = models.ForeignKey(
        "app.Aluno",
        on_delete=models.CASCADE,
        related_name="grades",
    )

    class Meta:
        verbose_name = "grade"
        verbose_name_plural = "grades"

    def clean(self):
        super().clean()
        self.periodo = (self.periodo or "").strip()
        if not self.periodo:
            raise ValidationError({"periodo": "O periodo nao pode ficar vazio."})

    def __str__(self):
        return f"{self.aluno} - {self.periodo}"
