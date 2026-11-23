from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("entrar/", views.CustomerLoginView.as_view(), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
    path("cadastro/", views.register, name="register"),
    path("perfil/", views.profile, name="profile"),
]
