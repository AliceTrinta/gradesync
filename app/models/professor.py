import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Professor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    avaliacao = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )

    class Meta:
        verbose_name = "professor"
        verbose_name_plural = "professores"

    def clean(self):
        super().clean()
        self.nome = (self.nome or "").strip()
        if not self.nome:
            raise ValidationError({"nome": "O nome nao pode ficar vazio."})

    def __str__(self):
        return self.nome
