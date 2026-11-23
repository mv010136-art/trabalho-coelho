from django import forms
from django.utils import timezone

from core.forms import BootstrapFormMixin

from .models import Reservation


class ReservationForm(BootstrapFormMixin, forms.ModelForm):
    """Formulário do cliente: veículo e cliente vêm da view, não do formulário."""

    start_date = forms.DateField(
        label="Data de retirada",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    end_date = forms.DateField(
        label="Data de devolução",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    class Meta:
        model = Reservation
        fields = ["start_date", "end_date", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, vehicle, customer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.vehicle = vehicle
        if customer is not None:
            self.instance.customer = customer

    def clean_start_date(self):
        start = self.cleaned_data["start_date"]
        # Numa reserva já existente a retirada pode estar no passado (reserva em
        # andamento). Nesse caso a data original continua válida; só uma nova
        # data de retirada precisa ser hoje ou no futuro.
        if self.instance.pk and start == self.instance.start_date:
            return start
        if start < timezone.localdate():
            raise forms.ValidationError("A data de retirada não pode estar no passado.")
        return start
