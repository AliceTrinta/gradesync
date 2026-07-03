import uuid

from django.db import models


class PreferenciaAcessibilidade(models.Model):
    """Preferencias de acessibilidade do aluno."""

    FONTE_PEQUENO = "pequeno"
    FONTE_MEDIO = "medio"
    FONTE_GRANDE = "grande"
    FONTE_MUITO_GRANDE = "muito-grande"

    TAMANHOS_FONTE = [
        (FONTE_PEQUENO, "Pequeno"),
        (FONTE_MEDIO, "Médio"),
        (FONTE_GRANDE, "Grande"),
        (FONTE_MUITO_GRANDE, "Muito grande"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.OneToOneField(
        "app.Aluno",
        on_delete=models.CASCADE,
        related_name="prefs_acessibilidade",
    )
    tamanho_fonte = models.CharField(
        max_length=16, choices=TAMANHOS_FONTE, default=FONTE_MEDIO
    )
    alto_contraste = models.BooleanField(default=False)
    reduzir_animacoes = models.BooleanField(default=False)
    sublinhar_links = models.BooleanField(default=False)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "preferencia de acessibilidade"
        verbose_name_plural = "preferencias de acessibilidade"

    def __str__(self):
        return f"Prefs acessibilidade de {self.aluno}"
