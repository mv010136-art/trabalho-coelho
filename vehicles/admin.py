from django.contrib import admin
from django.utils.html import format_html

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail",
        "name",
        "brand",
        "plate",
        "category",
        "seats",
        "daily_rate",
        "is_active",
        "created_at",
    )
    list_display_links = ("thumbnail", "name")
    list_filter = ("is_active", "category", "transmission", "fuel", "brand")
    list_editable = ("is_active",)
    search_fields = ("name", "brand", "plate", "description")
    readonly_fields = ("created_at", "updated_at", "likes_total")
    exclude = ("likes",)
    ordering = ("name",)

    @admin.display(description="foto")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:3px;">', obj.image.url
            )
        return "—"

    @admin.display(description="curtidas")
    def likes_total(self, obj):
        return obj.likes.count() if obj.pk else 0
