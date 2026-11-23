import datetime

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from reservations.models import Reservation
from vehicles.models import Vehicle

from .decorators import staff_required
from .forms import ContactForm
from .models import ContactMessage
from .utils import paginate


def home(request):
    fleet = Vehicle.objects.active()
    counts = dict(fleet.order_by().values_list("category").annotate(n=Count("id")))
    context = {
        "featured": fleet.with_rented_now().with_likes_count().order_by("-created_at", "-id")[:4],
        "fleet_count": fleet.count(),
        "brand_count": fleet.order_by().values("brand").distinct().count(),
        "tiles": [
            {"value": value, "label": label, "count": counts.get(value, 0)}
            for value, label in Vehicle.Category.choices
        ],
    }
    return render(request, "core/home.html", context)


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Mensagem enviada! Responderemos em breve.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


# --------------------------------------------------------------------------
# Painel da equipe (is_staff)
# --------------------------------------------------------------------------
@staff_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    counted = Reservation.objects.filter(status__in=Reservation.ACTIVE_STATUSES)

    # Receita do mês corrente: reservas (não canceladas) com retirada no mês.
    next_month_start = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    revenue_month = counted.filter(start_date__gte=month_start, start_date__lt=next_month_start)

    since = today - datetime.timedelta(days=6)
    daily_sales = (
        counted.filter(created_at__date__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total_reservations=Count("id"), total_value=Sum("total_price"))
        .order_by("-day")
    )

    context = {
        "vehicles_total": Vehicle.objects.count(),
        "vehicles_active": Vehicle.objects.filter(is_active=True).count(),
        "rented_now": Vehicle.objects.active().with_rented_now().filter(rented_now=True).count(),
        "reservations_confirmed": Reservation.objects.filter(
            status=Reservation.Status.CONFIRMED
        ).count(),
        "revenue_month": revenue_month.aggregate(total=Sum("total_price"))["total"] or 0,
        "pickups_today": Reservation.objects.filter(
            status=Reservation.Status.CONFIRMED, start_date=today
        ).select_related("customer__user", "vehicle"),
        "returns_today": Reservation.objects.filter(
            status=Reservation.Status.CONFIRMED, end_date=today
        ).select_related("customer__user", "vehicle"),
        "daily_sales": daily_sales,
        "messages_total": ContactMessage.objects.count(),
        "today": today,
    }
    return render(request, "core/dashboard.html", context)


@staff_required
def panel_vehicles(request):
    queryset = Vehicle.objects.with_rented_now().with_likes_count().order_by("-created_at", "-id")
    term = request.GET.get("q", "").strip()
    if term:
        queryset = queryset.search(term)
    page_obj = paginate(request, queryset, per_page=15)
    return render(request, "core/panel_vehicles.html", {"page_obj": page_obj, "q": term})


@staff_required
def panel_reservations(request):
    queryset = Reservation.objects.select_related("customer__user", "vehicle")
    status = request.GET.get("status", "")
    if status in Reservation.Status.values:
        queryset = queryset.filter(status=status)
    term = request.GET.get("q", "").strip()
    if term:
        queryset = queryset.filter(
            Q(vehicle__name__icontains=term)
            | Q(vehicle__brand__icontains=term)
            | Q(vehicle__plate__icontains=term.replace("-", "").upper())
            | Q(customer__user__username__icontains=term)
            | Q(customer__user__first_name__icontains=term)
            | Q(customer__user__last_name__icontains=term)
            | Q(customer__phone__icontains=term)
        )
    page_obj = paginate(request, queryset, per_page=15)
    context = {
        "page_obj": page_obj,
        "q": term,
        "status": status,
        "status_choices": Reservation.Status.choices,
    }
    return render(request, "core/panel_reservations.html", context)


@staff_required
def panel_messages(request):
    page_obj = paginate(request, ContactMessage.objects.all(), per_page=15)
    return render(request, "core/panel_messages.html", {"page_obj": page_obj})


@staff_required
@require_POST
def message_delete(request, pk):
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    contact_message.delete()
    messages.success(request, "Mensagem excluída.")
    return redirect("core:panel_messages")
