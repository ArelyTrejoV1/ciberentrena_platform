"""
Paso 1 de 2 para activar 2FA de un usuario: crea un dispositivo TOTP
SIN confirmar y muestra el código QR (como archivo PNG) y la URL
otpauth:// para agregarlo a una app autenticadora (Google Authenticator,
Authy, 1Password, etc.). El dispositivo queda inactivo hasta que se
confirme con `confirmar_dispositivo_2fa` usando un código real generado
por la app — así no puedes "casi" activar 2FA sin haberlo probado.

Uso:
    python manage.py tenant_command crear_dispositivo_2fa --schema=pyme_piloto --username=admin
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Crea (sin confirmar) un dispositivo TOTP para un usuario."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)

    def handle(self, *args, **options):
        try:
            usuario = Usuario.objects.get(username=options["username"])
        except Usuario.DoesNotExist:
            raise CommandError(f"No existe el usuario '{options['username']}' en este tenant.")

        device, creado = TOTPDevice.objects.get_or_create(
            user=usuario, name="default", defaults={"confirmed": False}
        )
        if not creado and device.confirmed:
            self.stdout.write(self.style.WARNING(
                "Este usuario ya tiene un dispositivo 2FA confirmado. "
                "Si necesitas reemplazarlo, bórralo primero desde el admin."
            ))
            return

        url = device.config_url
        self.stdout.write(f"Escanea esto con tu app autenticadora (Google Authenticator, Authy, etc.):\n")
        self.stdout.write(url)

        try:
            import qrcode
            ruta = f"/tmp/qr_2fa_{usuario.username}.png"
            qrcode.make(url).save(ruta)
            self.stdout.write(self.style.SUCCESS(f"\nQR guardado en: {ruta} (cópialo a tu máquina para escanearlo)."))
        except ImportError:
            pass

        self.stdout.write(
            "\nDespués de escanearlo, confirma con el código de 6 dígitos que te muestre la app:\n"
            f"  python manage.py tenant_command confirmar_dispositivo_2fa --schema=<schema> "
            f"--username={usuario.username} --token=123456"
        )
