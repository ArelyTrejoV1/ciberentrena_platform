"""
Middleware liviano que registra logins exitosos/fallidos automáticamente.
Para acciones de negocio (generar/enviar campaña, exportar datos), se
llama a `registrar` directamente desde la vista/tarea correspondiente
(ver apps/campaigns) — ahí sí hace falta el contexto específico.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .models import RegistroAuditoria


def _ip_del_request(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def log_login_exitoso(sender, request, user, **kwargs):
    RegistroAuditoria.objects.create(
        usuario=user,
        accion=RegistroAuditoria.ACCION_LOGIN_EXITOSO,
        ip_origen=_ip_del_request(request),
    )


@receiver(user_login_failed)
def log_login_fallido(sender, credentials, request, **kwargs):
    RegistroAuditoria.objects.create(
        usuario=None,
        accion=RegistroAuditoria.ACCION_LOGIN_FALLIDO,
        detalle={"username_intentado": credentials.get("username", "")},
        ip_origen=_ip_del_request(request) if request else None,
    )


class AuditLogMiddleware:
    """Placeholder de middleware — la lógica real va por señales (arriba).
    Se deja la clase para reservar el punto de extensión (ej. loguear
    accesos a rutas sensibles por path) sin tener que tocar MIDDLEWARE
    en settings más adelante."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
