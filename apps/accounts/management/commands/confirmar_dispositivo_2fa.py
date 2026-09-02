"""
Paso 2 de 2: confirma el dispositivo TOTP verificando un código real
generado por la app autenticadora. Solo tras esto el usuario queda
"verificado" y puede pasar el OTPAdminSite (admin en modo producción).

Uso:
    python manage.py tenant_command confirmar_dispositivo_2fa --schema=pyme_piloto --username=admin --token=123456
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Confirma un dispositivo TOTP previamente creado, verificando un token real."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--token", required=True)

    def handle(self, *args, **options):
        try:
            usuario = Usuario.objects.get(username=options["username"])
        except Usuario.DoesNotExist:
            raise CommandError(f"No existe el usuario '{options['username']}' en este tenant.")

        try:
            device = TOTPDevice.objects.get(user=usuario, name="default")
        except TOTPDevice.DoesNotExist:
            raise CommandError(
                "No hay dispositivo pendiente. Corre primero crear_dispositivo_2fa."
            )

        if device.verify_token(options["token"]):
            device.confirmed = True
            device.save(update_fields=["confirmed"])
            usuario.doble_factor_habilitado = True
            usuario.save(update_fields=["doble_factor_habilitado"])
            self.stdout.write(self.style.SUCCESS(
                f"2FA confirmado y activado para '{usuario.username}'."
            ))
        else:
            raise CommandError(
                "El código no es válido (¿expiró? generan uno nuevo cada 30s). Intenta de nuevo."
            )
