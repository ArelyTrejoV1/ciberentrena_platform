"""
Carga (o actualiza) el dataset base de plantillas en el tenant ACTUAL.
Se corre una vez por cada tenant nuevo (ej. dentro de tenant_command o
via `python manage.py tenant_command cargar_plantillas --schema=pyme_piloto`).

Uso:
    python manage.py cargar_plantillas
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.campaigns.models import PlantillaPhishing

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "plantillas_mx.json"


class Command(BaseCommand):
    help = "Carga el dataset base de plantillas de phishing MX en el tenant actual."

    def handle(self, *args, **options):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        creadas, actualizadas = 0, 0
        for p in data["plantillas"]:
            _, created = PlantillaPhishing.objects.update_or_create(
                clave=p["clave"],
                defaults={
                    "canal": p["canal"],
                    "categoria": p["categoria"],
                    "dificultad": p["dificultad"],
                    "asunto": p.get("asunto", ""),
                    "cuerpo": p["cuerpo"],
                    "variables": p.get("variables", []),
                    "senales_alerta": p.get("senales_alerta", []),
                    "activa": True,
                },
            )
            creadas += created
            actualizadas += not created

        self.stdout.write(self.style.SUCCESS(
            f"Plantillas: {creadas} creadas, {actualizadas} actualizadas."
        ))
