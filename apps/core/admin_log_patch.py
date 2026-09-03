"""
Bug real encontrado en producción (3-sep-2026): al editar cualquier
objeto desde /admin/ estando autenticado con un Usuario que vive en el
schema de un tenant (admin_pyme/empleado), Django revienta con:

    IntegrityError: insert or update on table "django_admin_log"
    violates foreign key constraint
    "django_admin_log_user_id_..._fk_accounts_usuario_id"
    DETAIL: Key (user_id)=(N) is not present in table "accounts_usuario".

Causa raíz (incompatibilidad conocida de django-tenants + AUTH_USER_MODEL
tenant-aware, ver apps/accounts/models.py): `apps.accounts` está en
SHARED_APPS y en TENANT_APPS a propósito, porque el rol SUPERADMIN vive
en el schema "public" y ADMIN_PYME/EMPLEADO viven aislados en el schema
de cada PyME (accounts_usuario es una tabla *distinta* por schema, con
ids independientes). Pero `django.contrib.admin` (LogEntry /
django_admin_log) solo está en SHARED_APPS, así que existe una única
tabla física, creada en "public", con su FK apuntando a
public.accounts_usuario. Cuando alguien logueado como usuario de un
tenant (id válido solo en ESE schema) guarda algo en /admin/, Django
intenta loguear la acción en esa tabla compartida con un user_id que no
existe en public.accounts_usuario -> IntegrityError.

No perdemos nada quitando este logging automático: las acciones que de
verdad importan para el proyecto (login, generación/envío de campañas,
aperturas/clics del simulacro) ya se registran de forma explícita y
tenant-aware en apps.audit.RegistroAuditoria (ver
apps/audit/middleware.py, apps/campaigns/services.py,
apps/campaigns/tracking.py). El "historial" nativo del admin
(django_admin_log) solo tenía sentido mientras todo el proyecto vivía
en un único schema; con multi-tenant real, lo deshabilitamos fuera de
"public" en vez de arriesgar una migración de datos bajo presión de
tiempo.
"""

from __future__ import annotations

from django.contrib import admin
from django.db import connection
from django_tenants.utils import get_public_schema_name


def _estamos_en_public() -> bool:
    return connection.schema_name == get_public_schema_name()


_log_addition_original = admin.ModelAdmin.log_addition
_log_change_original = admin.ModelAdmin.log_change
_log_deletion_original = admin.ModelAdmin.log_deletion
_log_deletions_original = getattr(admin.ModelAdmin, "log_deletions", None)


def _log_addition_parcheado(self, request, object, message):
    if not _estamos_en_public():
        return None
    return _log_addition_original(self, request, object, message)


def _log_change_parcheado(self, request, object, message):
    if not _estamos_en_public():
        return None
    return _log_change_original(self, request, object, message)


def _log_deletion_parcheado(self, request, object, object_repr):
    if not _estamos_en_public():
        return None
    return _log_deletion_original(self, request, object, object_repr)


admin.ModelAdmin.log_addition = _log_addition_parcheado
admin.ModelAdmin.log_change = _log_change_parcheado
admin.ModelAdmin.log_deletion = _log_deletion_parcheado

if _log_deletions_original is not None:

    def _log_deletions_parcheado(self, request, queryset):
        if not _estamos_en_public():
            return None
        return _log_deletions_original(self, request, queryset)

    admin.ModelAdmin.log_deletions = _log_deletions_parcheado
