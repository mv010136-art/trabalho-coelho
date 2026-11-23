from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from . import rules


class ReservationQuerySet(models.QuerySet):
    """Filtros usados no histórico (equivalem a ``rules.phase``)."""

    def upcoming(self):
        return self.filter(status="confirmed", start_date__gt=timezone.localdate())

    def in_progress(self):
        today = timezone.localdate()
        return self.filter(status="confirmed", start_date__lte=today, end_date__gt=today)

    def past(self):
        """Concluídas, ou confirmadas cuja devolução já passou."""
        return self.filter(
            Q(status="completed") | Q(status="confirmed", end_date__lte=timezone.localdate())
        )

    def cancelled(self):
        return self.filter(status="cancelled")


class Reservation(models.Model):
    """Reserva de um veículo por um cliente, com datas de retirada e devolução.

    O período é tratado como [retirada, devolução): o veículo fica ocupado a
    partir do dia da retirada e volta a ficar livre no dia da devolução, de
    modo que outra reserva pode começar no dia em que esta termina.
    """

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmada"
        CANCELLED = "cancelled", "Cancelada"
        COMPLETED = "completed", "Concluída"

    # Status que ocupam o veículo no calendário.
    ACTIVE_STATUSES = (Status.CONFIRMED, Status.COMPLETED)

    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name="cliente",
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name="veículo",
    )
    start_date = models.DateField("retirada")
    end_date = models.DateField("devolução")
    status = models.CharField(
        "situação", max_length=12, choices=Status.choices, default=Status.CONFIRMED
    )
    daily_rate = models.DecimalField(
        "diária (R$)", max_digits=8, decimal_places=2, null=True, blank=True, editable=False
    )
    total_price = models.DecimalField(
        "valor total (R$)", max_digits=10, decimal_places=2, default=0, editable=False
    )
    notes = models.TextField("observações", blank=True)
    created_at = models.DateTimeField("criada em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizada em", auto_now=True)

    objects = ReservationQuerySet.as_manager()

    PHASE_LABELS = {
        "upcoming": "Próxima",
        "in_progress": "Em andamento",
        "ended": "Encerrada",
        "completed": "Concluída",
        "cancelled": "Cancelada",
    }

    class Meta:
        verbose_name = "reserva"
        verbose_name_plural = "reservas"
        ordering = ["-start_date", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gt=F("start_date")),
                name="reservation_end_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["vehicle", "start_date", "end_date"], name="res_vehicle_period_idx"),
        ]

    def __str__(self):
        return f"Reserva #{self.pk}"

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_vehicle_id = instance.__dict__.get("vehicle_id")
        return instance

    # ---- regras de negócio ----------------------------------------------
    @classmethod
    def conflicts(cls, vehicle_id, start, end, exclude_pk=None):
        """Reservas que ocupam o veículo em algum dia de [start, end)."""
        queryset = cls.objects.filter(
            vehicle_id=vehicle_id,
            status__in=cls.ACTIVE_STATUSES,
            start_date__lt=end,
            end_date__gt=start,
        )
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset

    @property
    def days(self):
        return rules.rental_days(self.start_date, self.end_date)

    @property
    def phase(self):
        return rules.phase(self.status, self.start_date, self.end_date, timezone.localdate())

    @property
    def phase_label(self):
        return self.PHASE_LABELS[self.phase]

    @property
    def can_self_service(self):
        """O cliente pode alterar/cancelar sozinho até o dia anterior à retirada."""
        return rules.can_self_service(
            self.status == self.Status.CONFIRMED, self.start_date, timezone.localdate()
        )

    def user_can_manage(self, user):
        return bool(
            user.is_authenticated and (user.is_staff or self.customer.user_id == user.pk)
        )

    def user_can_modify(self, user):
        """Pode editar/cancelar? Equipe: qualquer confirmada; cliente: até a véspera."""
        if not self.user_can_manage(user):
            return False
        if user.is_staff:
            return self.status == self.Status.CONFIRMED
        return self.can_self_service

    def get_absolute_url(self):
        return reverse("reservations:detail", args=[self.pk])

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError(
                {"end_date": "A data de devolução deve ser posterior à data de retirada."}
            )
        if (
            self.vehicle_id
            and self.start_date
            and self.end_date
            and self.status in self.ACTIVE_STATUSES
        ):
            if self.conflicts(self.vehicle_id, self.start_date, self.end_date, self.pk).exists():
                raise ValidationError(
                    "Este veículo já está reservado em pelo menos um dia do período escolhido."
                )
            if self._state.adding and not self.vehicle.is_active:
                raise ValidationError("Este veículo não está disponível para locação.")

    def save(self, *args, **kwargs):
        vehicle_changed = getattr(self, "_loaded_vehicle_id", None) != self.vehicle_id
        if self._state.adding or self.daily_rate is None or vehicle_changed:
            # "Congela" a diária no momento da reserva.
            self.daily_rate = self.vehicle.daily_rate
        self.total_price = rules.calculate_total(self.daily_rate, self.start_date, self.end_date)
        super().save(*args, **kwargs)
        self._loaded_vehicle_id = self.vehicle_id
