"""Settings de desarrollo local. NUNCA usar esta configuración en un
servidor con datos reales de clientes."""

from .base import *  # noqa: F401,F403
from .base import env, INSTALLED_APPS, MIDDLEWARE

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
INTERNAL_IPS = ["127.0.0.1"]

# Los correos se ven en la UI de MailHog (http://localhost:8025), nunca
# salen a internet — evita mandar correos reales por accidente en dev.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mailhog"
EMAIL_PORT = 1025
EMAIL_USE_TLS = False

# En dev los tenants usan hostnames tipo "pyme-piloto.localhost" servidos
# por runserver en el puerto 8000, sin TLS.
SITE_URL_SCHEME = "http"
SITE_URL_PORT = "8000"

# En dev sí queremos ver todo el detalle
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405

CORS_ALLOW_ALL_ORIGINS = True

# CSP relajado en dev para no pelear con el debug toolbar
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
