from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "driver_license", "created_at")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
        "driver_license",
    )
    list_select_related = ("user",)
    readonly_fields = ("created_at",)

    @admin.display(description="nome", ordering="user__first_name")
    def name(self, obj):
        return obj.full_name

    @admin.display(description="e-mail", ordering="user__email")
    def email(self, obj):
        return obj.user.email
