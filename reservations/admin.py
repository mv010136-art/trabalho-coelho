from django.contrib import admin, messages

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "vehicle",
        "start_date",
        "end_date",
        "days",
        "total_price",
        "status",
    )
    list_filter = ("status", "start_date", "vehicle")
    search_fields = (
        "customer__user__username",
        "customer__user__first_name",
        "customer__user__last_name",
        "customer__phone",
        "vehicle__name",
        "vehicle__plate",
    )
    autocomplete_fields = ("customer", "vehicle")
    date_hierarchy = "start_date"
    list_select_related = ("customer__user", "vehicle")
    readonly_fields = ("daily_rate", "total_price", "created_at", "updated_at")
    actions = ("mark_cancelled", "mark_completed")

    @admin.display(description="diárias")
    def days(self, obj):
        return obj.days

    @admin.action(description="Cancelar reservas selecionadas")
    def mark_cancelled(self, request, queryset):
        count = 0
        for reservation in queryset.filter(status=Reservation.Status.CONFIRMED):
            reservation.status = Reservation.Status.CANCELLED
            reservation.save()
            count += 1
        self.message_user(request, f"{count} reserva(s) cancelada(s).", messages.SUCCESS)

    @admin.action(description="Marcar reservas selecionadas como concluídas")
    def mark_completed(self, request, queryset):
        count = 0
        for reservation in queryset.filter(status=Reservation.Status.CONFIRMED):
            reservation.status = Reservation.Status.COMPLETED
            reservation.save()
            count += 1
        self.message_user(request, f"{count} reserva(s) concluída(s).", messages.SUCCESS)
