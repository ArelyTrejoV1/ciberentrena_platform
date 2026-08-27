from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "usuario", "accion", "ip_origen")
    list_filter = ("accion",)
    search_fields = ("usuario__username", "ip_origen")
    readonly_fields = [f.name for f in RegistroAuditoria._meta.fields]

    def has_add_permission(self, request):
        # La auditoría solo se crea por código, nunca manualmente desde el admin.
        return False

    def has_delete_permission(self, request, obj=None):
        # Nadie borra registros de auditoría desde la UI (integridad del log).
        return False
