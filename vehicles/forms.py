import re

from django import forms

from core.forms import BootstrapFormMixin

from .models import Vehicle, normalize_plate

PLATE_RE = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")  # ABC1234 ou ABC1D23


class VehicleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "image",
            "name",
            "brand",
            "plate",
            "category",
            "transmission",
            "fuel",
            "seats",
            "daily_rate",
            "description",
            "is_active",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_plate(self):
        plate = normalize_plate(self.cleaned_data["plate"])
        if not PLATE_RE.match(plate):
            raise forms.ValidationError(
                "Placa inválida. Use o formato ABC-1234 ou ABC1D23."
            )
        return plate


ORDER_CHOICES = [
    ("", "Ordem padrão"),
    ("price_asc", "Menor preço"),
    ("price_desc", "Maior preço"),
    ("popular", "Mais curtidos"),
    ("new", "Mais recentes"),
    ("name", "Nome (A–Z)"),
]


class VehicleSearchForm(BootstrapFormMixin, forms.Form):
    """Busca por texto, filtros do catálogo e período de disponibilidade."""

    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Nome, marca, placa, lugares..."}),
    )
    pickup = forms.DateField(
        label="Retirada",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    dropoff = forms.DateField(
        label="Devolução",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    category = forms.ChoiceField(
        label="Categoria", required=False, choices=[("", "Todas")] + Vehicle.Category.choices
    )
    brand = forms.ChoiceField(label="Marca", required=False, choices=[("", "Todas")])
    transmission = forms.ChoiceField(
        label="Câmbio", required=False, choices=[("", "Qualquer")] + Vehicle.Transmission.choices
    )
    min_seats = forms.IntegerField(
        label="Lugares (mín.)", required=False, min_value=1, max_value=60
    )
    max_price = forms.DecimalField(
        label="Diária até (R$)", required=False, min_value=0, max_digits=8, decimal_places=2
    )
    order = forms.ChoiceField(label="Ordenar por", required=False, choices=ORDER_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        brands = (
            Vehicle.objects.active()
            .order_by("brand")
            .values_list("brand", flat=True)
            .distinct()
        )
        self.fields["brand"].choices = [("", "Todas")] + [(b, b) for b in brands]

    def clean(self):
        cleaned = super().clean()
        pickup, dropoff = cleaned.get("pickup"), cleaned.get("dropoff")
        if bool(pickup) != bool(dropoff):
            raise forms.ValidationError(
                "Para filtrar por disponibilidade informe as duas datas: retirada e devolução."
            )
        if pickup and dropoff and dropoff <= pickup:
            raise forms.ValidationError("A devolução deve ser posterior à retirada.")
        return cleaned
