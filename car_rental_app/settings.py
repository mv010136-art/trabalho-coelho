"""
Configurações do projeto Online Car Rental System (Django 5.2 LTS).

Valores sensíveis ou que mudam entre ambientes são lidos de variáveis de
ambiente (veja o arquivo .env.example). Sem nenhuma variável definida o
projeto roda em modo de desenvolvimento com SQLite.
"""
import os
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------
# Segurança
# --------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", True)

_DEV_SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", _DEV_SECRET_KEY)
if not DEBUG and SECRET_KEY == _DEV_SECRET_KEY:
    raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY quando DJANGO_DEBUG=False.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# Ative DJANGO_HTTPS=True quando o site for servido por HTTPS.
if env_bool("DJANGO_HTTPS", False):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --------------------------------------------------------------------------
# Aplicativos
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Aplicativos do projeto
    "core",
    "accounts",
    "vehicles",
    "reservations",
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

ROOT_URLCONF = "car_rental_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "car_rental_app.wsgi.application"

# --------------------------------------------------------------------------
# Banco de dados
# SQLite por padrão. Para PostgreSQL defina DB_ENGINE=postgresql e
# DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT (requer psycopg).
# --------------------------------------------------------------------------
_DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").lower()

if _DB_ENGINE in {"postgresql", "postgres"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "car_rental"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
elif _DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        }
    }
else:
    raise ImproperlyConfigured("DB_ENGINE deve ser 'sqlite' ou 'postgresql'.")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Autenticação
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "vehicles:list"
LOGOUT_REDIRECT_URL = "core:home"

# --------------------------------------------------------------------------
# Internacionalização
# --------------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Arquivos estáticos e de mídia
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Bootstrap 3 usa "danger" no lugar de "error".
MESSAGE_TAGS = {messages.ERROR: "danger"}
