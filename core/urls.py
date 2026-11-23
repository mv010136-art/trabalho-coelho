from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("contato/", views.contact, name="contact"),
    path("painel/", views.dashboard, name="dashboard"),
    path("painel/veiculos/", views.panel_vehicles, name="panel_vehicles"),
    path("painel/reservas/", views.panel_reservations, name="panel_reservations"),
    path("painel/mensagens/", views.panel_messages, name="panel_messages"),
    path("painel/mensagens/<int:pk>/excluir/", views.message_delete, name="message_delete"),
]
