from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import RegexValidator
from django.db import transaction

from core.forms import BootstrapFormMixin

from .models import Customer

User = get_user_model()

phone_validator = RegexValidator(
    r"^[0-9()+\-\s]{8,20}$",
    "Informe um telefone válido (somente números, espaços, parênteses, + e -).",
)


def _email_in_use(email, exclude_pk=None):
    queryset = User.objects.filter(email__iexact=email)
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    return queryset.exists()


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    username = forms.CharField(label="Usuário", widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(
        label="Senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )
    error_messages = {
        "invalid_login": "Usuário ou senha incorretos. Verifique e tente novamente.",
        "inactive": "Esta conta está inativa.",
    }


class CustomerRegistrationForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail")
    phone = forms.CharField(label="Telefone", max_length=20, validators=[phone_validator])
    address = forms.CharField(
        label="Endereço", required=False, widget=forms.Textarea(attrs={"rows": 2})
    )
    driver_license = forms.CharField(label="CNH", max_length=20, required=False)

    field_order = [
        "username", "first_name", "last_name", "email",
        "phone", "address", "driver_license", "password1", "password2",
    ]

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {"username": "Usuário"}

    def clean_email(self):
        email = self.cleaned_data["email"]
        if _email_in_use(email):
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=True)
        Customer.objects.create(
            user=user,
            phone=self.cleaned_data["phone"],
            address=self.cleaned_data.get("address", ""),
            driver_license=self.cleaned_data.get("driver_license", ""),
        )
        return user


class UserProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if _email_in_use(email, exclude_pk=self.instance.pk):
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email


class CustomerProfileForm(BootstrapFormMixin, forms.ModelForm):
    phone = forms.CharField(label="Telefone", max_length=20, validators=[phone_validator])

    class Meta:
        model = Customer
        fields = ("phone", "address", "driver_license")
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}
        labels = {"address": "Endereço", "driver_license": "CNH"}
