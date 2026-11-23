from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.reservation_list, name="list"),
    path("veiculo/<int:vehicle_pk>/reservar/", views.reservation_create, name="create"),
    path("<int:pk>/", views.reservation_detail, name="detail"),
    path("<int:pk>/editar/", views.reservation_update, name="update"),
    path("<int:pk>/cancelar/", views.reservation_cancel, name="cancel"),
    path("<int:pk>/concluir/", views.reservation_complete, name="complete"),
]
