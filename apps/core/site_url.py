"""
Construye la URL pública (esquema + host) del tenant ACTUAL a partir de
su Dominio primario (django-tenants). Se usa para armar los enlaces de
tracking dentro de los correos de campaña — tanto desde una vista (que
sí tiene request) como desde una tarea de Celery (que no lo tiene), por
eso no dependemos de request.build_absolute_uri().
"""

from __future__ import annotations

from django.conf import settings
from django.db import connection


def url_base_tenant_actual() -> str:
    dominio = (
        connection.tenant.domains.filter(is_primary=True).first()
        or connection.tenant.domains.first()
    )
    host = dominio.domain if dominio else "localhost"

    puerto = getattr(settings, "SITE_URL_PORT", "")
    if puerto:
        host = f"{host}:{puerto}"

    return f"{settings.SITE_URL_SCHEME}://{host}"
