"""
Envío real de una campaña por correo (Fase 2). Antes esto era el
TODO de campaigns/tasks.py — ahora es una función reutilizable tanto
por la tarea de Celery (envío async, uso normal) como por el comando
`enviar_campana` (envío síncrono, útil para el piloto/demo sin depender
de que el worker de Celery esté corriendo).

Solo se implementa el canal de correo (SMTP) en esta fase — SMS y
WhatsApp (Twilio) quedan para cuando haya presupuesto/cuenta de prueba,
tal como se decidió para priorizar tener el flujo completo funcionando
a tiempo (envío -> tracking -> dashboard).
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from apps.campaigns.models import Campana, PlantillaPhishing
from apps.core.site_url import url_base_tenant_actual

from .services import marcar_campana_enviada

logger = logging.getLogger(__name__)


def _construir_cuerpo_html(mensaje, base_url: str) -> str:
    clic_url = base_url + reverse("tracking:clic", args=[mensaje.token])
    pixel_url = base_url + reverse("tracking:apertura", args=[mensaje.token])

    texto = escape(mensaje.cuerpo_final)

    if mensaje.link_falso_visible:
        link_visible_escapado = escape(mensaje.link_falso_visible)
        # El texto que VE el empleado sigue pareciendo el link falso
        # original (mismo truco que un ataque real); el href de verdad
        # apunta a nuestro endpoint de tracking.
        texto = texto.replace(
            link_visible_escapado,
            f'<a href="{clic_url}">{link_visible_escapado}</a>',
        )

    html = texto.replace("\n", "<br>\n")
    html += (
        f'\n<img src="{pixel_url}" width="1" height="1" alt="" style="display:none">'
    )
    return html


def enviar_campana_real(campana: Campana, usuario_responsable=None) -> dict:
    """Envía todos los mensajes pendientes (enviado_en vacío) de una
    campaña. Devuelve un resumen {enviados, omitidos, fallidos} — nunca
    lanza una excepción por un mensaje individual fallido, para que un
    correo mal configurado no tumbe el resto del envío."""
    base_url = url_base_tenant_actual()

    mensajes = campana.mensajes.select_related("empleado__usuario", "plantilla").filter(
        enviado_en__isnull=True
    )

    enviados, omitidos, fallidos = 0, 0, 0
    detalle_omitidos = []
    detalle_fallidos = []

    conexion = get_connection()
    conexion.open()
    try:
        for mensaje in mensajes:
            if mensaje.plantilla.canal != PlantillaPhishing.CANAL_EMAIL:
                omitidos += 1
                detalle_omitidos.append(
                    {"mensaje_id": mensaje.id, "motivo": "canal no soportado en Fase 2"}
                )
                continue

            destinatario = mensaje.empleado.usuario.email
            if not destinatario:
                omitidos += 1
                detalle_omitidos.append(
                    {
                        "mensaje_id": mensaje.id,
                        "motivo": "empleado sin correo registrado",
                    }
                )
                continue

            asunto = (
                mensaje.asunto_final or f"[Simulacro] {mensaje.plantilla.categoria}"
            )

            try:
                correo = EmailMultiAlternatives(
                    subject=asunto,
                    body=mensaje.cuerpo_final,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[destinatario],
                    connection=conexion,
                )
                correo.attach_alternative(
                    _construir_cuerpo_html(mensaje, base_url), "text/html"
                )
                correo.send()
            except (
                Exception
            ) as exc:  # noqa: BLE001 — un correo roto no debe tumbar el resto
                fallidos += 1
                detalle_fallidos.append({"mensaje_id": mensaje.id, "error": str(exc)})
                logger.exception(
                    "Error enviando MensajeCampana id=%s a %s", mensaje.id, destinatario
                )
                continue

            mensaje.enviado_en = timezone.now()
            mensaje.save(update_fields=["enviado_en"])
            enviados += 1
    finally:
        conexion.close()

    resumen = {
        "enviados": enviados,
        "omitidos": omitidos,
        "fallidos": fallidos,
        "detalle_omitidos": detalle_omitidos,
        "detalle_fallidos": detalle_fallidos,
    }
    marcar_campana_enviada(
        campana, usuario_responsable=usuario_responsable, detalle_extra=resumen
    )
    return resumen
