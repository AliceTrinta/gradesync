import uuid

from django.core.exceptions import ValidationError
from django.db import models


class CargaHoraria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dia = models.CharField(max_length=16)
    hora_inicio = models.TimeField()
    hora_final = models.TimeField()

    class Meta:
        verbose_name = "carga horaria"
        verbose_name_plural = "cargas horarias"

    def clean(self):
        super().clean()
        self.dia = (self.dia or "").strip()
        if not self.dia:
            raise ValidationError({"dia": "O dia nao pode ficar vazio."})
        if self.hora_inicio and self.hora_final and self.hora_final <= self.hora_inicio:
            raise ValidationError(
                {"hora_final": "A hora final deve ser maior que a hora inicial."}
            )

    def __str__(self):
        return f"{self.dia} {self.hora_inicio}-{self.hora_final}"
