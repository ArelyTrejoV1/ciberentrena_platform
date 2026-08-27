"""Settings de producción. Aquí vive el "hardening" real — revisa este
archivo con calma antes del primer despliegue con clientes reales."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# --- HTTPS / cookies ---
# La app corre detrás de Nginx, que es quien realmente termina TLS; este
# header le dice a Django que confíe en X-Forwarded-Proto para saber si
# el request original era HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# HSTS: le dice al navegador que SIEMPRE use HTTPS con este dominio.
# Empieza en un valor bajo, súbelo cuando confirmes que todo funciona con
# HTTPS de forma estable (evita quedar "bloqueada" fuera de tu propio
# dominio si algo sale mal con el certificado).
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- CORS: solo el/los dominios reales del frontend, nunca "*" en prod ---
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_ALL_ORIGINS = False

# --- Sentry (opcional, activar cuando SENTRY_DSN esté configurado) ---
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,  # no mandar datos personales a un tercero
    )

LOGGING["root"]["level"] = "INFO"  # noqa: F405

# El admin exige 2FA verificado en produccion (aplicado via
# docker/gunicorn_conf.py -> apps/core/otp_hook.py, que corre en cada
# worker de gunicorn). Antes de activar esto en un servidor real,
# enrola tu dispositivo con crear_dispositivo_2fa + confirmar_dispositivo_2fa
# (ver PRODUCCION.md) -- si lo activas sin un dispositivo confirmado,
# quedas fuera del admin.
OTP_ADMIN_ENFORCED = True

