from rest_framework import permissions, viewsets

from .models import ScoreRiesgo
from .serializers import ScoreRiesgoSerializer


class EsAdminPymeOSuperadmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in ("admin_pyme", "superadmin")
        )


class ScoreRiesgoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScoreRiesgoSerializer
    permission_classes = [EsAdminPymeOSuperadmin]
    queryset = ScoreRiesgo.objects.select_related("empleado__usuario").all()
