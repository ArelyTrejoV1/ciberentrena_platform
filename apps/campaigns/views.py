from rest_framework import permissions, viewsets

from .models import Campana
from .serializers import CampanaSerializer


class EsAdminPymeOSuperadmin(permissions.BasePermission):
    """Solo admin_pyme y superadmin pueden ver/crear campañas — un
    empleado normal nunca debe poder listar campañas de la empresa."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in ("admin_pyme", "superadmin")
        )


class CampanaViewSet(viewsets.ReadOnlyModelViewSet):
    """De solo lectura por ahora: la creación de campañas se hace vía
    management command / panel admin mientras no exista el flujo de
    autoservicio completo (Fase 2)."""

    serializer_class = CampanaSerializer
    permission_classes = [EsAdminPymeOSuperadmin]

    def get_queryset(self):
        return Campana.objects.all().order_by("-fecha_creacion")
