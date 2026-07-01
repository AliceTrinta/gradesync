"""Signals — auto-cria preferências default quando um Aluno é criado."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models import Aluno, PreferenciaAcessibilidade, PreferenciaConta


@receiver(post_save, sender=Aluno)
def criar_preferencias_default(sender, instance, created, **kwargs):
    """Ao criar um Aluno, cria seus perfis de preferencias padrao."""
    if not created:
        return
    PreferenciaAcessibilidade.objects.get_or_create(aluno=instance)
    PreferenciaConta.objects.get_or_create(aluno=instance)
