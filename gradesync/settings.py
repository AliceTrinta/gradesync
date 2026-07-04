import sys
from pathlib import Path

from decouple import Csv, config


BASE_DIR = Path(__file__).resolve().parent.parent


def _bool_env(key, default):
    """Cast tolerante: se o env var vier com valor invalido (ex.: outra app do
    sistema usando o mesmo nome), silenciosamente cai no default.
    """
    raw = config(key, default=default)
    if isinstance(raw, bool):
        return raw
    valores_true = {"1", "true", "yes", "on", "sim"}
    valores_false = {"0", "false", "no", "off", "nao"}
    normalizado = str(raw).strip().lower()
    if normalizado in valores_true:
        return True
    if normalizado in valores_false:
        return False
    return default


SECRET_KEY = config("SECRET_KEY", default="dev-only-secret-key")
DEBUG = _bool_env("DEBUG", default=True)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=Csv(),
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app.apps.GradeSyncConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gradesync.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "app.context_processors.gradesync_context",
            ],
        },
    },
]

WSGI_APPLICATION = "gradesync.wsgi.application"

if "test" in sys.argv:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "app:login"
LOGIN_REDIRECT_URL = "app:home"

EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="GradeSync <no-reply@gradesync.local>",
)

AI_PROVIDER = config("AI_PROVIDER", default="gemini")
AI_API_KEY = config("AI_API_KEY", default="")
AI_MODEL = config("AI_MODEL", default="gemini-2.5-flash")
AI_TIMEOUT_SECONDS = config("AI_TIMEOUT_SECONDS", default=30, cast=int)
AI_MAX_TOKENS = config("AI_MAX_TOKENS", default=4096, cast=int)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "gradesync-locmem",
    }
}

