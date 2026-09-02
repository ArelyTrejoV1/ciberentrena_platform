"""URLs que ve un usuario DENTRO de un tenant (una PyME cliente):
login, dashboard, campañas, scoring, API."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("api/campaigns/", include("apps.campaigns.urls")),
    path("api/scoring/", include("apps.scoring.urls")),
    path("healthz/", include("apps.core.urls")),
    # Públicas (sin login) — las visita el correo/navegador del empleado
    # que recibe el simulacro, nunca un cliente autenticado. Ver
    # ARCHITECTURE.md sección de tracking (Fase 2).
    path("t/", include("apps.campaigns.tracking_urls")),
    path("dashboard/", include("apps.campaigns.dashboard_urls")),
]

if settings.DEBUG:
    # INSTALLED_APPS/MIDDLEWARE de dev.py ya activan django-debug-toolbar,
    # pero sin esta línea CUALQUIER página en desarrollo truena con
    # NoReverseMatch('djdt') al intentar dibujar la barra — faltaba
    # registrar sus URLs. Nunca se activa en producción (DEBUG=False).
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
