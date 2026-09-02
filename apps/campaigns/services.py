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
    ronda: int = 1,
) -> Campana:
    if not consentimiento_explicito:
        raise ConsentimientoRequeridoError(
            "No se puede crear una campaña sin consentimiento explícito de la empresa piloto."
        )

    campana = Campana(
        nombre=nombre, creada_por=creada_por, consentimiento_explicito=True, ronda=ronda
    )
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
        raise ValidationError(
            "No hay plantillas activas que coincidan con los filtros indicados."
        )

    provider = provider or RuleBasedProvider(seed=seed)

    import random

    rng = random.Random(seed)

    mensajes = []
    for empleado in empleados:
        plantilla = rng.choice(plantillas)
        asunto, cuerpo, link_falso = provider.generar(plantilla, empleado)
        mensajes.append(
            MensajeCampana(
                campana=campana,
                empleado=empleado,
                plantilla=plantilla,
                asunto_final=asunto or "",
                cuerpo_final=cuerpo,
                link_falso_visible=link_falso or "",
            )
        )
    MensajeCampana.objects.bulk_create(mensajes)

    RegistroAuditoria.objects.create(
        usuario=creada_por,
        accion=RegistroAuditoria.ACCION_CAMPANA_GENERADA,
        detalle={
            "campana_id": campana.id,
            "n_mensajes": len(mensajes),
            "nombre": nombre,
        },
    )

    return campana


def marcar_campana_enviada(
    campana: Campana, usuario_responsable=None, detalle_extra: dict = None
):
    """Se llama al terminar de enviar una campaña (ver campaigns.sending).
    El 'enviado_en' de cada MensajeCampana ya se marca individualmente
    durante el envío real, aquí solo se cierra la campaña como tal."""
    campana.fecha_envio = timezone.now()
    campana.save(update_fields=["fecha_envio"])

    detalle = {"campana_id": campana.id}
    detalle.update(detalle_extra or {})

    RegistroAuditoria.objects.create(
        usuario=usuario_responsable,
        accion=RegistroAuditoria.ACCION_CAMPANA_ENVIADA,
        detalle=detalle,
    )
