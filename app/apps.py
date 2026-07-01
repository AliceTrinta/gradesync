from django.apps import AppConfig


class GradeSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        # Registra signal handlers (auto-cria PreferenciaAcessibilidade/PreferenciaConta).
        from app import signals  # noqa: F401
