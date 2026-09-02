"""
Vistas de autenticación. Se usa el LoginView de Django (ya maneja CSRF,
redirect seguro, y hashing de contraseña) envuelto con rate limiting
para mitigar fuerza bruta / credential stuffing contra el login — un
punto de entrada obligado a proteger en cualquier producto que va a
vender acceso a datos de terceros.
"""

from django.contrib.auth.views import LoginView, LogoutView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class LoginSeguroView(LoginView):
    template_name = "accounts/login.html"


class LogoutSeguroView(LogoutView):
    pass
