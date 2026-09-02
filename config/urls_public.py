"""URLs del schema "public": aquí vive la gestión de clientes (altas de
PyMEs) y el login del superadmin. Los usuarios de una PyME nunca ven
estas rutas — solo se sirven cuando el request llega por el dominio
raíz de la plataforma, no por el subdominio de un tenant."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("healthz/", include("apps.core.urls")),
]

if settings.DEBUG:
    # Ver la nota equivalente en config/urls.py — mismo problema, mismo fix.
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
