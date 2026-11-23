from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.formats import number_format
from django.views.decorators.http import require_POST

from accounts.models import Customer
from core.decorators import staff_required
from core.utils import paginate, redirect_back
from vehicles.models import Vehicle

from .forms import ReservationForm
from .models import Reservation


def _get_reservation_for(user, pk):
    """Reserva visível ao usuário (dono ou equipe); caso contrário 404."""
    queryset = Reservation.objects.select_related("customer__user", "vehicle")
    if not user.is_staff:
        queryset = queryset.filter(customer__user=user)
    return get_object_or_404(queryset, pk=pk)


@login_required
def reservation_create(request, vehicle_pk):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_pk)
    if not vehicle.is_active:
        raise Http404("Veículo indisponível.")
    customer, _ = Customer.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Trava a linha do veículo (PostgreSQL) para que duas reservas simultâneas
        # do mesmo carro sejam validadas uma de cada vez.
        with transaction.atomic():
            locked = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
            form = ReservationForm(request.POST, vehicle=locked, customer=customer)
            if form.is_valid():
                reservation = form.save()
                messages.success(
                    request,
                    f"Reserva #{reservation.pk} confirmada! Total: R$ {number_format(reservation.total_price, 2)}.",
                )
                return redirect(reservation)
    else:
        form = ReservationForm(
            initial={
                "start_date": request.GET.get("pickup"),
                "end_date": request.GET.get("dropoff"),
            },
            vehicle=vehicle,
            customer=customer,
        )
    return render(
        request,
        "reservations/form.html",
        {"form": form, "vehicle": vehicle, "title": f"Reservar {vehicle.name}"},
    )


HISTORY_FILTERS = [
    ("all", "Todas"),
    ("upcoming", "Próximas"),
    ("in_progress", "Em andamento"),
    ("past", "Concluídas"),
    ("cancelled", "Canceladas"),
]


@login_required
def reservation_list(request):
    """Histórico do cliente, com abas por situação e resumo de valores."""
    base = Reservation.objects.filter(customer__user=request.user).select_related("vehicle")
    current = request.GET.get("f", "all")
    if current not in dict(HISTORY_FILTERS):
        current = "all"
    queryset = base if current == "all" else getattr(base, current)()

    tabs = [
        {
            "key": key,
            "label": label,
            "count": base.count() if key == "all" else getattr(base, key)().count(),
        }
        for key, label in HISTORY_FILTERS
    ]
    total = base.filter(status__in=Reservation.ACTIVE_STATUSES).aggregate(total=Sum("total_price"))
    return render(
        request,
        "reservations/list.html",
        {
            "page_obj": paginate(request, queryset, per_page=10),
            "tabs": tabs,
            "current": current,
            "total_booked": total["total"] or 0,
        },
    )


@login_required
def reservation_detail(request, pk):
    reservation = _get_reservation_for(request.user, pk)
    return render(
        request,
        "reservations/detail.html",
        {
            "reservation": reservation,
            "can_modify": reservation.user_can_modify(request.user),
            "today": timezone.localdate(),
        },
    )


@login_required
def reservation_update(request, pk):
    reservation = _get_reservation_for(request.user, pk)
    if not reservation.user_can_modify(request.user):
        messages.error(
            request,
            "Esta reserva não pode mais ser alterada pelo site. Entre em contato conosco.",
        )
        return redirect(reservation)

    if request.method == "POST":
        with transaction.atomic():
            Vehicle.objects.select_for_update().get(pk=reservation.vehicle_id)
            form = ReservationForm(request.POST, instance=reservation, vehicle=reservation.vehicle)
            if form.is_valid():
                form.save()
                messages.success(request, "Reserva atualizada.")
                return redirect(reservation)
    else:
        form = ReservationForm(instance=reservation, vehicle=reservation.vehicle)
    return render(
        request,
        "reservations/form.html",
        {
            "form": form,
            "vehicle": reservation.vehicle,
            "reservation": reservation,
            "title": f"Alterar reserva #{reservation.pk}",
        },
    )


@login_required
def reservation_cancel(request, pk):
    reservation = _get_reservation_for(request.user, pk)
    if not reservation.user_can_modify(request.user):
        messages.error(
            request,
            "Esta reserva não pode mais ser cancelada pelo site. Entre em contato conosco.",
        )
        return redirect(reservation)
    if request.method == "POST":
        reservation.status = Reservation.Status.CANCELLED
        reservation.save()
        messages.success(request, f"Reserva #{reservation.pk} cancelada.")
        return redirect_back(request, "reservations:list")
    return render(request, "reservations/confirm_cancel.html", {"reservation": reservation})


@staff_required
@require_POST
def reservation_complete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.status != Reservation.Status.CONFIRMED:
        messages.error(request, "Somente reservas confirmadas podem ser concluídas.")
    else:
        reservation.status = Reservation.Status.COMPLETED
        reservation.save()
        messages.success(request, f"Reserva #{reservation.pk} marcada como concluída.")
    return redirect_back(request, "core:panel_reservations")
