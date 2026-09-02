"""
Modulo dedicado (archivo nuevo, ver nota en apps/audit/apps.py sobre por
que vive aqui) que envuelve el admin de Django con OTPAdminSite cuando
settings.OTP_ADMIN_ENFORCED es True (prod.py). Se importa desde
config/wsgi.py, que es el punto de entrada real cuando gunicorn sirve
la app en produccion.
"""

from django.conf import settings


def aplicar_otp_admin_si_corresponde():
    if not getattr(settings, "OTP_ADMIN_ENFORCED", False):
        return
    from django.contrib import admin
    from django_otp.admin import OTPAdminSite

    if not isinstance(admin.site, OTPAdminSite):
        admin.site.__class__ = OTPAdminSite
