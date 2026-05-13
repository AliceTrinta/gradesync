import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Disciplina(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=32, unique=True)
    nome = models.CharField(max_length=255)
    taxa_de_reprovacao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    pre_requisitos = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="dependentes",
    )

    class Meta:
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"

    def clean(self):
        super().clean()
        self.codigo = (self.codigo or "").strip()
        self.nome = (self.nome or "").strip()
        if not self.codigo:
            raise ValidationError({"codigo": "O codigo nao pode ficar vazio."})
        if not self.nome:
            raise ValidationError({"nome": "O nome nao pode ficar vazio."})

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
