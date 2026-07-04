import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from app.exceptions import AIProviderError
from app.services import AIService


class Command(BaseCommand):
    help = "Testa conectividade com o provedor de IA (Gemini)."

    def handle(self, *args, **options):
        if not settings.AI_API_KEY:
            raise CommandError(
                "AI_API_KEY vazia. Defina no .env (ver .env.example) para "
                "habilitar a IA."
            )

        self.stdout.write(
            f"Ping IA -> provedor={settings.AI_PROVIDER}, "
            f"modelo={settings.AI_MODEL}, "
            f"timeout={settings.AI_TIMEOUT_SECONDS}s"
        )

        service = AIService()
        prompt = "Responda apenas com a palavra ok em minusculas, sem pontuacao."

        inicio = time.perf_counter()
        try:
            texto = service._chamar_gemini(
                prompt, esperar_json=False, tag="ai_ping"
            )
        except AIProviderError as exc:
            raise CommandError(f"Falha ao chamar IA: {exc}") from exc
        elapsed = time.perf_counter() - inicio

        preview = (texto or "").strip()[:100]
        self.stdout.write(self.style.SUCCESS(
            f"OK em {elapsed*1000:.0f} ms -> {preview!r}"
        ))
