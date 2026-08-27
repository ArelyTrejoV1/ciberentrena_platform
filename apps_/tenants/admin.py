from django.contrib import admin

from .models import Cliente, Dominio


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre_empresa", "schema_name", "plan", "activo", "fecha_alta")
    list_filter = ("plan", "activo")
    search_fields = ("nombre_empresa", "rfc", "contacto_email")


@admin.register(Dominio)
class DominioAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
