"""
Envía (de forma SÍNCRONA, sin depender de que el worker de Celery esté
levantado) los mensajes pendientes de una campaña ya creada. Pensado
para el piloto/demo: correrlo justo antes de la presentación en vivo.

Para producción real, sigue existiendo la tarea async equivalente
(campaigns.tasks.enviar_campana_task) — úsala desde una vista/admin
action para no bloquear la request HTTP.

Uso:
    python manage.py tenant_command enviar_campana --campana-id=1 --schema=pyme_piloto
    python manage.py tenant_command enviar_campana --nombre="Campaña demo — piloto" --schema=pyme_piloto
"""

from django.core.management.base import BaseCommand, CommandError

from apps.campaigns.models import Campana
from apps.campaigns.sending import enviar_campana_real


class Command(BaseCommand):
    help = "Envía por correo los mensajes pendientes de una campaña (síncrono, para demo/piloto)."

    def add_arguments(self, parser):
        parser.add_argument("--campana-id", type=int, default=None)
        parser.add_argument(
            "--nombre",
            type=str,
            default=None,
            help="Nombre exacto de la campaña, si no conoces el id.",
        )

    def handle(self, *args, **options):
        if options["campana_id"]:
            campana = Campana.objects.filter(id=options["campana_id"]).first()
        elif options["nombre"]:
            campana = (
                Campana.objects.filter(nombre=options["nombre"])
                .order_by("-fecha_creacion")
                .first()
            )
        else:
            raise CommandError('Indica --campana-id=<id> o --nombre="<nombre exacto>".')

        if not campana:
            raise CommandError("No se encontró esa campaña en este tenant.")

        if not campana.consentimiento_explicito:
            raise CommandError(
                "Esta campaña no tiene consentimiento explícito registrado — no se envía."
            )

        self.stdout.write(f"Enviando campaña '{campana.nombre}' (id={campana.id})...")
        resumen = enviar_campana_real(campana)

        self.stdout.write(
            self.style.SUCCESS(
                f"Enviados: {resumen['enviados']} | Omitidos: {resumen['omitidos']} | Fallidos: {resumen['fallidos']}"
            )
        )
        for o in resumen["detalle_omitidos"]:
            self.stdout.write(
                self.style.WARNING(
                    f"  Omitido mensaje {o['mensaje_id']}: {o['motivo']}"
                )
            )
        for f in resumen["detalle_fallidos"]:
            self.stdout.write(
                self.style.ERROR(f"  Falló mensaje {f['mensaje_id']}: {f['error']}")
            )
