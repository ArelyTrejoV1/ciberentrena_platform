"""Settings de desarrollo local. NUNCA usar esta configuración en un
servidor con datos reales de clientes."""

from .base import *  # noqa: F401,F403
from .base import env, INSTALLED_APPS, MIDDLEWARE

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
INTERNAL_IPS = ["127.0.0.1"]

# Por default los correos se ven en la UI de MailHog (http://localhost:8025)
# y nunca salen a internet, para no mandar correos reales por accidente en
# desarrollo local puro. PERO si ya pusiste un proveedor real (Brevo, etc.)
# en tu .env, esos valores tienen prioridad — así el envío real (Fase 2)
# funciona aunque sigas usando settings.dev en el piloto/demo, sin tener
# que activar config.settings.prod (que trae HTTPS obligatorio, 2FA
# forzado en el admin, etc. — no listo todavía para el pitch).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="mailhog")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)

# En dev los tenants usan hostnames tipo "pyme-piloto.localhost" servidos
# por runserver en el puerto 8000, sin TLS.
SITE_URL_SCHEME = "http"
SITE_URL_PORT = "8000"

# En dev sí queremos ver todo el detalle
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405

CORS_ALLOW_ALL_ORIGINS = True

# CSP relajado en dev para no pelear con el debug toolbar
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
