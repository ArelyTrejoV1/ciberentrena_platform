"""
Dashboard HTML (server-side, sin frontend separado) para admin_pyme y
superadmin — resultados de campañas: tasa de apertura/clic/datos
ingresados por campaña, detalle por empleado, y comparación entre
rondas (medición antes/después de una capacitación, tal como pide el
roadmap de Fase 2).

Deliberadamente NO expone qué le pasó a un empleado específico a otro
empleado — solo admin_pyme/superadmin pueden ver esta sección (ver
apps.accounts.decorators.requiere_rol).
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404, render

from apps.accounts.decorators import requiere_rol
from apps.accounts.models import Usuario

from .models import Campana


def _tasas(campana: Campana) -> dict:
    total = campana.mensajes.count()
    if total == 0:
        return {
            "total": 0,
            "abiertos": 0,
            "caidos": 0,
            "con_dato": 0,
            "tasa_apertura": 0,
            "tasa_clic": 0,
            "tasa_dato": 0,
        }

    abiertos = campana.mensajes.filter(abierto=True).count()
    caidos = campana.mensajes.filter(cayo=True).count()
    con_dato = campana.mensajes.filter(dato_ingresado=True).count()
    return {
        "total": total,
        "abiertos": abiertos,
        "caidos": caidos,
        "con_dato": con_dato,
        "tasa_apertura": round(100 * abiertos / total, 1),
        "tasa_clic": round(100 * caidos / total, 1),
        "tasa_dato": round(100 * con_dato / total, 1),
    }


@requiere_rol(Usuario.ADMIN_PYME, Usuario.SUPERADMIN)
def lista_campanas(request):
    campanas = Campana.objects.all().order_by("-fecha_creacion")
    filas = [{"campana": c, **_tasas(c)} for c in campanas]
    return render(request, "campaigns/dashboard_lista.html", {"filas": filas})


@requiere_rol(Usuario.ADMIN_PYME, Usuario.SUPERADMIN)
def detalle_campana(request, campana_id):
    campana = get_object_or_404(Campana, id=campana_id)
    mensajes = campana.mensajes.select_related(
        "empleado__usuario", "plantilla"
    ).order_by("empleado__departamento", "empleado__usuario__last_name")
    return render(
        request,
        "campaigns/dashboard_detalle.html",
        {
            "campana": campana,
            "mensajes": mensajes,
            **_tasas(campana),
        },
    )


@requiere_rol(Usuario.ADMIN_PYME, Usuario.SUPERADMIN)
def comparativo_rondas(request):
    campanas = Campana.objects.all().order_by("ronda", "fecha_creacion")
    filas = [{"campana": c, **_tasas(c)} for c in campanas]

    mejora = None
    primera_con_datos = next((f for f in filas if f["total"] > 0), None)
    ultima_con_datos = next((f for f in reversed(filas) if f["total"] > 0), None)
    if (
        primera_con_datos
        and ultima_con_datos
        and primera_con_datos is not ultima_con_datos
    ):
        mejora = round(
            primera_con_datos["tasa_clic"] - ultima_con_datos["tasa_clic"], 1
        )

    return render(
        request,
        "campaigns/dashboard_comparativo.html",
        {"filas": filas, "mejora": mejora},
    )
