"""
Crea el schema "public" (obligatorio en django-tenants) y, opcionalmente,
un tenant piloto de ejemplo con su dominio. Pensado para el primer
arranque del proyecto en un servidor nuevo.

Uso:
    python manage.py bootstrap_tenants
    python manage.py bootstrap_tenants --piloto --dominio-piloto pyme-piloto.localhost
"""

from django.core.management.base import BaseCommand

from apps.tenants.models import Cliente, Dominio


class Command(BaseCommand):
    help = "Crea el schema public y (opcionalmente) un tenant piloto."

    def add_arguments(self, parser):
        parser.add_argument("--piloto", action="store_true", help="También crea un tenant piloto de ejemplo.")
        parser.add_argument("--dominio-publico", default="localhost")
        parser.add_argument("--dominio-piloto", default="pyme-piloto.localhost")
        parser.add_argument("--nombre-piloto", default="PyME Piloto")

    def handle(self, *args, **options):
        publico, creado = Cliente.objects.get_or_create(
            schema_name="public",
            defaults={"nombre_empresa": "CiberEntrena (plataforma)", "plan": Cliente.PLAN_PRO},
        )
        if creado:
            Dominio.objects.create(domain=options["dominio_publico"], tenant=publico, is_primary=True)
            self.stdout.write(self.style.SUCCESS("Schema public creado."))
        else:
            self.stdout.write("Schema public ya existía, se deja igual.")

        if options["piloto"]:
            piloto, creado = Cliente.objects.get_or_create(
                schema_name="pyme_piloto",
                defaults={"nombre_empresa": options["nombre_piloto"], "plan": Cliente.PLAN_PILOTO},
            )
            if creado:
                Dominio.objects.create(domain=options["dominio_piloto"], tenant=piloto, is_primary=True)
                self.stdout.write(self.style.SUCCESS(
                    f"Tenant piloto '{piloto.nombre_empresa}' creado en {options['dominio_piloto']}."
                ))
            else:
                self.stdout.write("El tenant piloto ya existía, se deja igual.")
