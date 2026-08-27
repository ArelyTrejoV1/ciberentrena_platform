"""
Capa de servicio: orquesta la creación de una campaña + sus mensajes.
Se llama desde una vista/comando/tarea de Celery, nunca se le pide al
modelo que haga esto (mantiene los modelos "delgados").
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import RegistroAuditoria

from .llm_hook import RuleBasedProvider
from .models import Campana, MensajeCampana, PerfilEmpleado, PlantillaPhishing


class ConsentimientoRequeridoError(Exception):
    pass


@transaction.atomic
def crear_campana(
    *,
    nombre: str,
    creada_por,
    empleados: list[PerfilEmpleado],
    consentimiento_explicito: bool,
    canal: str = None,
    categoria: str = None,
    dificultad: str = None,
    provider=None,
    seed: int = None,
) -> Campana:
    if not consentimiento_explicito:
        raise ConsentimientoRequeridoError(
            "No se puede crear una campaña sin consentimiento explícito de la empresa piloto."
        )

    campana = Campana(nombre=nombre, creada_por=creada_por, consentimiento_explicito=True)
    campana.full_clean()  # dispara Campana.clean(), doble verificación de consentimiento
    campana.save()

    qs = PlantillaPhishing.objects.filter(activa=True)
    if canal:
        qs = qs.filter(canal=canal)
    if categoria:
        qs = qs.filter(categoria=categoria)
    if dificultad:
        qs = qs.filter(dificultad=dificultad)
    plantillas = list(qs)
    if not plantillas:
        raise ValidationError("No hay plantillas activas que coincidan con los filtros indicados.")

    provider = provider or RuleBasedProvider(seed=seed)

    import random
    rng = random.Random(seed)

    mensajes = []
    for empleado in empleados:
        plantilla = rng.choice(plantillas)
        asunto, cuerpo = provider.generar(plantilla, empleado)
        mensajes.append(MensajeCampana(
            campana=campana,
            empleado=empleado,
            plantilla=plantilla,
            asunto_final=asunto or "",
            cuerpo_final=cuerpo,
        ))
    MensajeCampana.objects.bulk_create(mensajes)

    RegistroAuditoria.objects.create(
        usuario=creada_por,
        accion=RegistroAuditoria.ACCION_CAMPANA_GENERADA,
        detalle={"campana_id": campana.id, "n_mensajes": len(mensajes), "nombre": nombre},
    )

    return campana


def marcar_campana_enviada(campana: Campana, usuario_responsable=None):
    """Se llamará desde la tarea de Celery de envío real (Fase 2)."""
    campana.fecha_envio = timezone.now()
    campana.save(update_fields=["fecha_envio"])
    campana.mensajes.update(enviado_en=timezone.now())

    RegistroAuditoria.objects.create(
        usuario=usuario_responsable,
        accion=RegistroAuditoria.ACCION_CAMPANA_ENVIADA,
        detalle={"campana_id": campana.id},
    )
