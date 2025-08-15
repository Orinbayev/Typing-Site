"""
Django settings for typing_site project (SQLite + Render-friendly).
"""

from pathlib import Path
import os

# =========================
# Paths
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# Core config (ENV-first)
# =========================
def _split_env(name: str):
    val = os.environ.get(name, "")
    return [x.strip() for x in val.split(",") if x.strip()]

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-ONLY-dont-use-in-prod")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = _split_env("ALLOWED_HOSTS") or (["*"] if DEBUG else [])
CSRF_TRUSTED_ORIGINS = _split_env("CSRF_TRUSTED_ORIGINS")

# Render/Reverse proxy orqali HTTPS bo'lganda request.is_secure() to'g'ri ishlashi uchun
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Prod'da xavfsizlik flaglari (localda bezovta qilmaydi)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# =========================
# Applications
# =========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "typingapp.apps.TypingappConfig",
]

# =========================
# Middleware
# =========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # staticni WhiteNoise orqali beramiz
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =========================
# URLs / WSGI
# =========================
ROOT_URLCONF = "typing_site.urls"
WSGI_APPLICATION = "typing_site.wsgi.application"

# =========================
# Templates
# =========================
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

# =========================
# Database (SQLite on persistent disk)
# =========================
DB_DIR = Path(os.environ.get("DB_DIR", BASE_DIR / "data"))
DB_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DB_DIR / "db.sqlite3"),
    }
}

# =========================
# Password validation
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =========================
# I18N / TZ
# =========================
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# =========================
# Static & Media
# =========================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"          # collectstatic shu yerga yozadi
STATICFILES_DIRS = [BASE_DIR / "static"]        # agar /static kataloging bo'lsa
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))

# =========================
# Auth redirects
# =========================
LOGIN_URL = "typingapp:login"
LOGIN_REDIRECT_URL = "typingapp:center_list"
LOGOUT_REDIRECT_URL = "typingapp:login"

# =========================
# Defaults
# =========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEBUG = True
ALLOWED_HOSTS = ["*"]
