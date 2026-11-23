"""Rotas principais do projeto."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Car Rental — Administração"
admin.site.site_title = "Car Rental"
admin.site.index_title = "Painel administrativo"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("contas/", include("accounts.urls")),
    path("veiculos/", include("vehicles.urls")),
    path("reservas/", include("reservations.urls")),
]

if settings.DEBUG:
    # Servir uploads (fotos dos veículos) durante o desenvolvimento.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
