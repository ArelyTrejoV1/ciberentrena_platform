"""
Equivalente al main_demo.py del prototipo de Fase 1, ahora contra la
base de datos real del tenant. Crea (si no existen) 3 empleados de
prueba y genera una campaña de ejemplo.

Para el envío real (Fase 2) los empleados de prueba necesitan un
correo REAL al que puedas entrar durante el pitch en vivo — pásalos
con --correos, en el mismo orden que la lista interna (María, Jorge,
Paola). Si no se corre con este archivo, se puede correr después
directamente en el admin de Django editando el email de cada Usuario.

Uso:
    python manage.py generar_campana_demo
    python manage.py generar_campana_demo --correos correo1@gmail.com,correo2@gmail.com,correo3@gmail.com
    python manage.py generar_campana_demo --ronda=2 --correos ...   # segunda corrida, para comparar antes/después
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.campaigns.models import PerfilEmpleado
from apps.campaigns.services import ConsentimientoRequeridoError, crear_campana

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Genera una campaña de demostración con empleados de prueba."

    def add_arguments(self, parser):
        parser.add_argument(
            "--correos",
            type=str,
            default=None,
            help="Lista de correos reales separados por coma, para poder ver el simulacro llegar "
            "en vivo (ej. tus propios alias o los de tu equipo). Sin esto, los empleados demo "
            "quedan sin correo y el envío real (Fase 2) los omite.",
        )
        parser.add_argument(
            "--canal",
            type=str,
            default="email",
            help="Canal de las plantillas a usar (email/sms/whatsapp). Por default 'email', que es "
            "el único canal con envío + tracking real en esta fase — usa --canal='' para "
            "permitir los tres como en el prototipo original.",
        )
        parser.add_argument(
            "--ronda",
            type=int,
            default=1,
            help="Número de ronda (1 = primera corrida).",
        )
        parser.add_argument(
            "--nombre",
            type=str,
            default=None,
            help="Nombre de la campaña (por default incluye la ronda).",
        )

    def handle(self, *args, **options):
        datos_demo = [
            ("maria.lopez", "María", "López", "Finanzas"),
            ("jorge.ramirez", "Jorge", "Ramírez", "Ventas"),
            ("paola.gutierrez", "Paola", "Gutiérrez", "Recursos Humanos"),
        ]
        correos = (
            [c.strip() for c in options["correos"].split(",")]
            if options["correos"]
            else []
        )

        empleados = []
        for i, (username, nombre, apellido, depto) in enumerate(datos_demo):
            usuario, creado = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": nombre,
                    "last_name": apellido,
                    "rol": Usuario.EMPLEADO,
                },
            )
            if i < len(correos) and usuario.email != correos[i]:
                usuario.email = correos[i]
                usuario.save(update_fields=["email"])
            perfil, _ = PerfilEmpleado.objects.get_or_create(
                usuario=usuario,
                defaults={"departamento": depto, "antiguedad_meses": 12},
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

        nombre = (
            options["nombre"] or f"Campaña demo — piloto (ronda {options['ronda']})"
        )
        self.stdout.write("Generando campaña CON consentimiento explícito...")
        campana = crear_campana(
            nombre=nombre,
            creada_por=None,
            empleados=empleados,
            consentimiento_explicito=True,
            canal=options["canal"] or None,
            ronda=options["ronda"],
            seed=42,
        )

        for m in campana.mensajes.select_related("empleado__usuario", "plantilla"):
            self.stdout.write(
                f"\n--- {m.empleado} | {m.plantilla.clave} | {m.plantilla.canal} ---"
            )
            if m.asunto_final:
                self.stdout.write(f"Asunto: {m.asunto_final}")
            self.stdout.write(m.cuerpo_final)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCampaña '{campana.nombre}' creada con {campana.mensajes.count()} mensajes."
            )
        )
