from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, Exists, OuterRef, Q
from django.urls import reverse
from django.utils import timezone


def normalize_plate(value):
    """'abc-1d23' -> 'ABC1D23' (aceita placa antiga e Mercosul)."""
    return (value or "").replace("-", "").replace(" ", "").upper()


class VehicleQuerySet(models.QuerySet):
    def active(self):
        """Veículos que fazem parte da frota (podem ser alugados)."""
        return self.filter(is_active=True)

    def search(self, term):
        term = (term or "").strip()
        if not term:
            return self
        condition = (
            Q(name__icontains=term)
            | Q(brand__icontains=term)
            | Q(plate__icontains=normalize_plate(term))
            | Q(description__icontains=term)
        )
        if term.isdigit():
            condition |= Q(seats=int(term))
        return self.filter(condition)

    def available_between(self, start, end):
        """Veículos ativos sem reserva (confirmada/concluída) no período.

        Intervalos são [retirada, devolução): devolver no dia em que outro
        cliente retira é permitido.
        """
        from reservations.models import Reservation

        busy = Reservation.objects.filter(
            status__in=Reservation.ACTIVE_STATUSES,
            start_date__lt=end,
            end_date__gt=start,
        ).values("vehicle_id")
        return self.active().exclude(pk__in=busy)

    def with_rented_now(self):
        """Anota ``rented_now``: há reserva em andamento hoje?"""
        from reservations.models import Reservation

        today = timezone.localdate()
        in_progress = Reservation.objects.filter(
            vehicle=OuterRef("pk"),
            status__in=Reservation.ACTIVE_STATUSES,
            start_date__lte=today,
            end_date__gt=today,
        )
        return self.annotate(rented_now=Exists(in_progress))

    def with_likes_count(self):
        return self.annotate(likes_count=Count("likes", distinct=True))


class Vehicle(models.Model):
    class Category(models.TextChoices):
        ECONOMY = "economy", "Econômico"
        SEDAN = "sedan", "Sedã"
        SUV = "suv", "SUV"
        VAN = "van", "Van / Utilitário"
        PREMIUM = "premium", "Premium"

    class Transmission(models.TextChoices):
        MANUAL = "manual", "Manual"
        AUTOMATIC = "automatic", "Automático"

    class Fuel(models.TextChoices):
        FLEX = "flex", "Flex"
        GASOLINE = "gasoline", "Gasolina"
        DIESEL = "diesel", "Diesel"
        ELECTRIC = "electric", "Elétrico"
        HYBRID = "hybrid", "Híbrido"

    image = models.ImageField("foto", upload_to="vehicles/%Y/%m/", blank=True)
    name = models.CharField("nome do veículo", max_length=100)
    brand = models.CharField("marca", max_length=100)
    plate = models.CharField("placa", max_length=8, unique=True)
    category = models.CharField(
        "categoria", max_length=12, choices=Category.choices, default=Category.ECONOMY
    )
    transmission = models.CharField(
        "câmbio", max_length=12, choices=Transmission.choices, default=Transmission.MANUAL
    )
    fuel = models.CharField(
        "combustível", max_length=12, choices=Fuel.choices, default=Fuel.FLEX
    )
    seats = models.PositiveSmallIntegerField(
        "número de lugares",
        validators=[MinValueValidator(1), MaxValueValidator(60)],
    )
    daily_rate = models.DecimalField(
        "diária (R$)",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    description = models.TextField("descrição", blank=True)
    is_active = models.BooleanField(
        "ativo na frota",
        default=True,
        help_text="Desmarque para retirar o veículo da locação (manutenção, venda etc.).",
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_vehicles",
        blank=True,
        verbose_name="curtidas",
    )
    created_at = models.DateTimeField("cadastrado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    objects = VehicleQuerySet.as_manager()

    class Meta:
        verbose_name = "veículo"
        verbose_name_plural = "veículos"
        ordering = ["name", "id"]

    def __str__(self):
        return f"{self.name} ({self.plate})"

    def save(self, *args, **kwargs):
        self.plate = normalize_plate(self.plate)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("vehicles:detail", args=[self.pk])

    # ---- disponibilidade -------------------------------------------------
    def is_available_between(self, start, end, exclude_reservation=None):
        """True se o veículo está ativo e livre em [start, end)."""
        from reservations.models import Reservation

        if not self.is_active:
            return False
        conflicts = Reservation.conflicts(self.pk, start, end, exclude_pk=exclude_reservation)
        return not conflicts.exists()

    @property
    def is_rented_now(self):
        """Há uma reserva em andamento hoje? (usa a anotação quando existe)."""
        annotated = getattr(self, "rented_now", None)
        if annotated is not None:
            return annotated
        from reservations.models import Reservation

        today = timezone.localdate()
        return Reservation.objects.filter(
            vehicle=self,
            status__in=Reservation.ACTIVE_STATUSES,
            start_date__lte=today,
            end_date__gt=today,
        ).exists()

    @property
    def current_reservation(self):
        from reservations.models import Reservation

        today = timezone.localdate()
        return (
            Reservation.objects.filter(
                vehicle=self,
                status__in=Reservation.ACTIVE_STATUSES,
                start_date__lte=today,
                end_date__gt=today,
            )
            .order_by("end_date")
            .first()
        )

    @property
    def availability_label(self):
        if not self.is_active:
            return "Fora da frota"
        if self.is_rented_now:
            return "Alugado agora"
        return "Disponível"

    def upcoming_busy_periods(self, limit=10):
        """Períodos futuros já reservados (sem dados pessoais)."""
        from reservations.models import Reservation

        today = timezone.localdate()
        return Reservation.objects.filter(
            vehicle=self,
            status__in=Reservation.ACTIVE_STATUSES,
            end_date__gt=today,
        ).order_by("start_date")[:limit]
