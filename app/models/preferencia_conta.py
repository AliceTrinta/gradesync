import uuid

from django.db import models


class PreferenciaConta(models.Model):
    """Preferencias gerais de conta (idioma, tema)."""

    IDIOMA_PT_BR = "pt-BR"
    IDIOMA_EN_US = "en-US"
    IDIOMAS = [
        (IDIOMA_PT_BR, "Português (Brasil)"),
        (IDIOMA_EN_US, "English (US)"),
    ]

    TEMA_CLARO = "claro"
    TEMA_ESCURO = "escuro"
    TEMAS = [
        (TEMA_CLARO, "Claro"),
        (TEMA_ESCURO, "Escuro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.OneToOneField(
        "app.Aluno",
        on_delete=models.CASCADE,
        related_name="prefs_conta",
    )
    idioma = models.CharField(max_length=8, choices=IDIOMAS, default=IDIOMA_PT_BR)
    tema = models.CharField(max_length=16, choices=TEMAS, default=TEMA_CLARO)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "preferencia de conta"
        verbose_name_plural = "preferencias de conta"

    def __str__(self):
        return f"Prefs conta de {self.aluno}"
