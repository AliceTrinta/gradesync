from django.apps import AppConfig


class GradeSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        from app import signals  # noqa: F401
