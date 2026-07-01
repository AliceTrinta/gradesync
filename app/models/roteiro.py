import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Roteiro(models.Model):
    """Roteiro de estudo semanal do aluno.

    Slots são armazenados como JSON: lista de dicts com
    {dia, hora_inicio, hora_final, titulo, cor}.
    """

    CORES = [
        ("blue", "Azul"),
        ("green", "Verde"),
        ("purple", "Roxo"),
        ("red", "Vermelho"),
        ("orange", "Laranja"),
        ("yellow", "Amarelo"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.OneToOneField(
        "app.Aluno",
        on_delete=models.CASCADE,
        related_name="roteiro",
    )
    titulo = models.CharField(max_length=120, default="Meu roteiro semanal")
    slots = models.JSONField(default=list, blank=True)
    prompt_usado = models.TextField(blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "roteiro"
        verbose_name_plural = "roteiros"

    def clean(self):
        super().clean()
        self.titulo = (self.titulo or "").strip() or "Meu roteiro semanal"
        if not isinstance(self.slots, list):
            raise ValidationError({"slots": "Slots deve ser uma lista de blocos."})
        for i, slot in enumerate(self.slots):
            if not isinstance(slot, dict):
                raise ValidationError({"slots": f"Slot {i} deve ser um objeto."})
            for campo in ("dia", "hora_inicio", "hora_final", "titulo"):
                if not slot.get(campo):
                    raise ValidationError(
                        {"slots": f"Slot {i} sem campo obrigatorio '{campo}'."}
                    )

    def __str__(self):
        return f"Roteiro de {self.aluno}"
