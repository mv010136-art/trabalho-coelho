from django.urls import path

from . import views

app_name = "vehicles"

urlpatterns = [
    path("", views.vehicle_list, name="list"),
    path("novos/", views.vehicle_list, {"mode": "new"}, name="new"),
    path("populares/", views.vehicle_list, {"mode": "popular"}, name="popular"),
    path("novo/", views.vehicle_create, name="create"),
    path("<int:pk>/", views.vehicle_detail, name="detail"),
    path("<int:pk>/editar/", views.vehicle_update, name="update"),
    path("<int:pk>/excluir/", views.vehicle_delete, name="delete"),
    path("<int:pk>/curtir/", views.vehicle_like, name="like"),
]
