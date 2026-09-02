"""Tarea periódica (Celery Beat) para recalcular el scoring de riesgo.
Se registra en django-celery-beat vía el admin (Periodic Tasks) apuntando
a 'apps.scoring.tasks.recalcular_riesgo_task', ej. una vez por noche."""

from celery import shared_task
from django.core.management import call_command


@shared_task
def recalcular_riesgo_task():
    call_command("entrenar_modelo_riesgo")
    return {"estado": "modelo de riesgo recalculado"}
