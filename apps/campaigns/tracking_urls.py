"""
URLs públicas de tracking — deliberadamente cortas y sin prefijo /api/,
porque las visita el cliente de correo o el navegador del empleado, no
un cliente autenticado de la plataforma. Ver apps.campaigns.tracking.
"""

from django.urls import path

from . import tracking

app_name = "tracking"

urlpatterns = [
    path("o/<uuid:token>.gif", tracking.pixel_apertura, name="apertura"),
    path("c/<uuid:token>/", tracking.pagina_simulacro, name="clic"),
]
