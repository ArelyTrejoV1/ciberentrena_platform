"""
Vistas PÚBLICAS (sin login) que reciben las interacciones de un
empleado con un simulacro real: apertura del correo (pixel), clic en
el enlace falso, y envío del formulario de la página falsa.

Deliberadamente NO son parte de la API de DRF (apps.campaigns.views):
estas URLs las visita el cliente de correo o el navegador del empleado,
nunca un cliente autenticado de la plataforma.

Regla de seguridad no negociable (ver CHECKLIST_SEGURIDAD.md): jamás se
guarda el contenido de lo que el empleado escribe en el formulario de
la página falsa — solo el HECHO de que lo envió.
"""

from __future__ import annotations

import base64

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.audit.models import RegistroAuditoria

from .models import MensajeCampana

# GIF transparente de 1x1 — el "pixel" de apertura. No depende de un
# archivo estático para poder servirse desde una vista pública simple.
_PIXEL_1X1_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBTAA7"
)


def _ip_del_request(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@never_cache
def pixel_apertura(request, token):
    """Un <img> de 1x1 embebido en el correo. Si el cliente de correo
    carga imágenes remotas, esto marca 'abierto' — igual que hacen las
    plataformas comerciales de concientización."""
    mensaje = MensajeCampana.objects.filter(token=token).first()

    if mensaje and not mensaje.abierto:
        mensaje.abierto = True
        mensaje.fecha_apertura = timezone.now()
        mensaje.save(update_fields=["abierto", "fecha_apertura"])
        RegistroAuditoria.objects.create(
            usuario=None,
            accion=RegistroAuditoria.ACCION_SIMULACRO_APERTURA,
            detalle={"mensaje_id": mensaje.id, "campana_id": mensaje.campana_id},
            ip_origen=_ip_del_request(request),
        )

    return HttpResponse(_PIXEL_1X1_GIF, content_type="image/gif")


@never_cache
@require_http_methods(["GET", "POST"])
def pagina_simulacro(request, token):
    """GET: el empleado hizo clic en el enlace falso -> 'cayó'. Se le
    muestra una página que IMITA el engaño (nunca un formulario que
    pida contraseñas reales) con un botón de 'continuar'.

    POST: el empleado interactuó con esa página falsa (ej. dio clic en
    'Verificar mis datos') -> se registra el evento, se descarta
    cualquier dato del formulario sin leerlo ni guardarlo, y se muestra
    la revelación educativa con las señales de alerta de esa plantilla
    específica."""
    mensaje = get_object_or_404(
        MensajeCampana.objects.select_related("plantilla", "empleado__usuario"),
        token=token,
    )

    if request.method == "GET":
        if mensaje.cayo is not True:
            mensaje.cayo = True
            mensaje.fecha_resultado = timezone.now()
            mensaje.save(update_fields=["cayo", "fecha_resultado"])
            RegistroAuditoria.objects.create(
                usuario=None,
                accion=RegistroAuditoria.ACCION_SIMULACRO_CLIC,
                detalle={
                    "mensaje_id": mensaje.id,
                    "campana_id": mensaje.campana_id,
                    "plantilla": mensaje.plantilla.clave,
                },
                ip_origen=_ip_del_request(request),
            )
        return render(
            request,
            "campaigns/pagina_falsa.html",
            {
                "plantilla": mensaje.plantilla,
                "token": token,
            },
        )

    # POST — deliberadamente NUNCA se lee request.POST más allá de esta
    # línea de comentario: no se inspecciona, no se guarda, no se loguea
    # su contenido. Solo se registra que el evento ocurrió.
    if not mensaje.dato_ingresado:
        mensaje.dato_ingresado = True
        mensaje.fecha_dato_ingresado = timezone.now()
        mensaje.save(update_fields=["dato_ingresado", "fecha_dato_ingresado"])
        RegistroAuditoria.objects.create(
            usuario=None,
            accion=RegistroAuditoria.ACCION_SIMULACRO_DATO_INGRESADO,
            detalle={
                "mensaje_id": mensaje.id,
                "campana_id": mensaje.campana_id,
                "plantilla": mensaje.plantilla.clave,
            },
            ip_origen=_ip_del_request(request),
        )

    return render(
        request,
        "campaigns/revelacion.html",
        {
            "plantilla": mensaje.plantilla,
            "empleado": mensaje.empleado,
        },
    )
