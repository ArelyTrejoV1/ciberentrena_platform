"""
Tareas asíncronas de Celery. El envío real (SMTP/Twilio) es Fase 2 —
por ahora se deja el esqueleto para que la arquitectura async ya esté
lista y solo haya que rellenar la integración de envío.
"""

from celery import shared_task


@shared_task
def enviar_campana_task(campana_id: int):
    """Envía (Fase 2: SMTP para email, Twilio para SMS/WhatsApp) todos los
    mensajes de una campaña sin bloquear la request HTTP que la disparó."""
    from .models import Campana
    from .services import marcar_campana_enviada

    campana = Campana.objects.get(id=campana_id)
    # TODO Fase 2: iterar campana.mensajes.all() y enviar por el canal
    # correspondiente (smtplib/django.core.mail para email, Twilio API
    # para sms/whatsapp), registrando enviado_en por mensaje.
    marcar_campana_enviada(campana)
    return {"campana_id": campana_id, "estado": "enviada (stub, Fase 2 pendiente)"}
