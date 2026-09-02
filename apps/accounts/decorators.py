"""
Decoradores de autorización por rol. Úsalos en las vistas de dashboard
(Fase 2) para no depender solo del middleware — defensa en profundidad:
aunque alguien manipule la sesión, la vista vuelve a verificar el rol.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def requiere_rol(*roles_permitidos):
    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(request, *args, **kwargs):
            if request.user.rol not in roles_permitidos:
                raise PermissionDenied("No tienes permiso para acceder a esta sección.")
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def requiere_doble_factor(vista):
    """Exige que el usuario haya verificado su 2FA en la sesión actual.
    Aplicar a vistas de superadmin/admin_pyme en cuanto se active 2FA
    obligatorio para esos roles."""
    @wraps(vista)
    @login_required
    def envoltura(request, *args, **kwargs):
        if not request.user.is_verified():
            raise PermissionDenied("Verifica tu segundo factor de autenticación para continuar.")
        return vista(request, *args, **kwargs)
    return envoltura
