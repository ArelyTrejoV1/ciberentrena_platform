"""
Usuario personalizado con roles. Vive tanto en el schema "public"
(donde solo existen usuarios con rol SUPERADMIN, quien administra
clientes/tenants) como en el schema de cada tenant (donde existen
ADMIN_PYME y EMPLEADO, aislados por completo de los de otras PyMEs).

Por qué un modelo de usuario personalizado desde el día 1: cambiar
AUTH_USER_MODEL después de tener usuarios reales en producción es una
migración muy dolorosa en Django. Aunque hoy solo se necesiten estos
tres roles, definirlo así desde el inicio evita ese problema.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    SUPERADMIN = "superadmin"
    ADMIN_PYME = "admin_pyme"
    EMPLEADO = "empleado"
    ROL_CHOICES = [
        (SUPERADMIN, "Superadmin (CiberEntrena)"),
        (ADMIN_PYME, "Administrador de la PyME"),
        (EMPLEADO, "Empleado"),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default=EMPLEADO)
    telefono = models.CharField(max_length=20, blank=True)

    # Reforzado a nivel de aplicación además del middleware de django-otp:
    # true una vez que el usuario configuró y verificó su segundo factor.
    doble_factor_habilitado = models.BooleanField(default=False)

    @property
    def es_superadmin(self) -> bool:
        return self.rol == self.SUPERADMIN

    @property
    def es_admin_pyme(self) -> bool:
        return self.rol == self.ADMIN_PYME

    @property
    def es_empleado(self) -> bool:
        return self.rol == self.EMPLEADO

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"
