from django.urls import path

from .views import LoginSeguroView, LogoutSeguroView

app_name = "accounts"

urlpatterns = [
    path("login/", LoginSeguroView.as_view(), name="login"),
    path("logout/", LogoutSeguroView.as_view(), name="logout"),
]
