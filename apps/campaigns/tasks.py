"""
Tareas asíncronas de Celery. El envío real por correo (Fase 2) vive en
apps.campaigns.sending — esta tarea solo se encarga de correr esa
lógica en el schema del tenant correcto y sin bloquear la request HTTP
que la disparó. SMS/WhatsApp (Twilio) quedan pendientes de presupuesto.
"""

from celery import shared_task
from django_tenants.utils import schema_context


@shared_task
def enviar_campana_task(campana_id: int, schema_name: str):
    """schema_name es obligatorio: un worker de Celery no sabe en qué
    tenant está parado por sí solo (a diferencia de una vista HTTP, que
    lo resuelve TenantMainMiddleware) — hay que decírselo explícitamente."""
    with schema_context(schema_name):
        from .models import Campana
        from .sending import enviar_campana_real

        campana = Campana.objects.get(id=campana_id)
        resumen = enviar_campana_real(campana)
        return {"campana_id": campana_id, **resumen}
