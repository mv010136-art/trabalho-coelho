from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.decorators import staff_required
from core.utils import paginate, redirect_back

from .forms import VehicleForm, VehicleSearchForm
from .models import Vehicle

LIST_MODES = {
    "all": {"title": "Veículos", "subtitle": "Toda a frota disponível para locação."},
    "new": {"title": "Novidades", "subtitle": "Veículos adicionados mais recentemente."},
    "popular": {"title": "Mais curtidos", "subtitle": "Os preferidos dos nossos clientes."},
}


def vehicle_list(request, mode="all"):
    form = VehicleSearchForm(request.GET or None)
    queryset = Vehicle.objects.active().with_rented_now().with_likes_count()
    dates_qs = ""

    if form.is_valid():
        data = form.cleaned_data
        if data.get("q"):
            queryset = queryset.search(data["q"])
        for field in ("category", "transmission"):
            if data.get(field):
                queryset = queryset.filter(**{field: data[field]})
        if data.get("brand"):
            queryset = queryset.filter(brand__iexact=data["brand"])
        if data.get("min_seats"):
            queryset = queryset.filter(seats__gte=data["min_seats"])
        if data.get("max_price") is not None:
            queryset = queryset.filter(daily_rate__lte=data["max_price"])
        if data.get("pickup") and data.get("dropoff"):
            queryset = queryset.filter(
                pk__in=Vehicle.objects.available_between(data["pickup"], data["dropoff"]).values("pk")
            )
            dates_qs = urlencode(
                {"pickup": data["pickup"].isoformat(), "dropoff": data["dropoff"].isoformat()}
            )
    # Se o formulário é inválido (datas incoerentes) mostramos o erro e a lista completa.

    order = form.cleaned_data.get("order") if form.is_valid() else ""
    orderings = {
        "price_asc": ("daily_rate", "name", "id"),
        "price_desc": ("-daily_rate", "name", "id"),
        "popular": ("-likes_count", "name", "id"),
        "new": ("-created_at", "-id"),
        "name": ("name", "id"),
    }
    if not order:
        order = {"new": "new", "popular": "popular"}.get(mode, "name")
    queryset = queryset.order_by(*orderings[order])

    context = {
        "form": form,
        "page_obj": paginate(request, queryset, per_page=12),
        "mode": mode,
        "dates_qs": dates_qs,
        "filters_active": form.is_valid()
        and any(form.cleaned_data.get(f) not in (None, "") for f in ("q", "category", "brand", "transmission", "min_seats", "max_price", "pickup")),
        **LIST_MODES[mode],
    }
    return render(request, "vehicles/list.html", context)


def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if not vehicle.is_active and not request.user.is_staff:
        raise Http404("Veículo indisponível.")
    context = {
        "vehicle": vehicle,
        "likes_count": vehicle.likes.count(),
        "liked": request.user.is_authenticated and vehicle.likes.filter(pk=request.user.pk).exists(),
        "busy_periods": vehicle.upcoming_busy_periods(),
        "today": timezone.localdate(),
    }
    return render(request, "vehicles/detail.html", context)


@staff_required
def vehicle_create(request):
    form = VehicleForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        vehicle = form.save()
        messages.success(request, f"Veículo “{vehicle.name}” cadastrado.")
        return redirect("core:panel_vehicles")
    return render(request, "vehicles/form.html", {"form": form, "title": "Novo veículo"})


@staff_required
def vehicle_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    form = VehicleForm(request.POST or None, request.FILES or None, instance=vehicle)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Veículo “{vehicle.name}” atualizado.")
        return redirect("core:panel_vehicles")
    return render(
        request,
        "vehicles/form.html",
        {"form": form, "title": f"Editar {vehicle.name}", "vehicle": vehicle},
    )


@staff_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == "POST":
        name = vehicle.name
        try:
            vehicle.delete()
        except ProtectedError:
            messages.error(
                request,
                f"“{name}” possui reservas e não pode ser excluído. "
                "Desmarque “ativo na frota” para retirá-lo da locação.",
            )
            return redirect("core:panel_vehicles")
        messages.success(request, f"Veículo “{name}” excluído.")
        return redirect("core:panel_vehicles")
    return render(request, "vehicles/confirm_delete.html", {"vehicle": vehicle})


@login_required
@require_POST
def vehicle_like(request, pk):
    vehicle = get_object_or_404(Vehicle.objects.active(), pk=pk)
    if vehicle.likes.filter(pk=request.user.pk).exists():
        vehicle.likes.remove(request.user)
    else:
        vehicle.likes.add(request.user)
    return redirect_back(request, "vehicles:detail", vehicle.pk)
