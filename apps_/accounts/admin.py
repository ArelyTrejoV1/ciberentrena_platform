from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "is_active", "doble_factor_habilitado")
    list_filter = ("rol", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("CiberEntrena", {"fields": ("rol", "telefono", "doble_factor_habilitado")}),
    )
