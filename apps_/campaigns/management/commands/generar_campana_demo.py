"""
Equivalente al main_demo.py del prototipo de Fase 1, ahora contra la
base de datos real del tenant. Crea (si no existen) 3 empleados de
prueba y genera una campaña de ejemplo.

Uso:
    python manage.py generar_campana_demo
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.campaigns.models import PerfilEmpleado
from apps.campaigns.services import ConsentimientoRequeridoError, crear_campana

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Genera una campaña de demostración con empleados de prueba."

    def handle(self, *args, **options):
        datos_demo = [
            ("maria.lopez", "María", "López", "Finanzas"),
            ("jorge.ramirez", "Jorge", "Ramírez", "Ventas"),
            ("paola.gutierrez", "Paola", "Gutiérrez", "Recursos Humanos"),
        ]
        empleados = []
        for username, nombre, apellido, depto in datos_demo:
            usuario, _ = Usuario.objects.get_or_create(
                username=username,
                defaults={"first_name": nombre, "last_name": apellido, "rol": Usuario.EMPLEADO},
            )
            perfil, _ = PerfilEmpleado.objects.get_or_create(
                usuario=usuario, defaults={"departamento": depto, "antiguedad_meses": 12}
            )
            empleados.append(perfil)

        self.stdout.write("Intentando SIN consentimiento (debe fallar)...")
        try:
            crear_campana(
                nombre="Demo sin consentimiento",
                creada_por=None,
                empleados=empleados,
                consentimiento_explicito=False,
            )
        except ConsentimientoRequeridoError as e:
            self.stdout.write(self.style.WARNING(f"Bloqueado correctamente: {e}"))

        self.stdout.write("Generando campaña CON consentimiento explícito...")
        campana = crear_campana(
            nombre="Campaña demo — piloto",
            creada_por=None,
            empleados=empleados,
            consentimiento_explicito=True,
            seed=42,
        )

        for m in campana.mensajes.select_related("empleado__usuario", "plantilla"):
            self.stdout.write(f"\n--- {m.empleado} | {m.plantilla.clave} | {m.plantilla.canal} ---")
            if m.asunto_final:
                self.stdout.write(f"Asunto: {m.asunto_final}")
            self.stdout.write(m.cuerpo_final)

        self.stdout.write(self.style.SUCCESS(f"\nCampaña '{campana.nombre}' creada con {campana.mensajes.count()} mensajes."))
