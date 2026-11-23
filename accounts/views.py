from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import (
    CustomerProfileForm,
    CustomerRegistrationForm,
    LoginForm,
    UserProfileForm,
)
from .models import Customer


class CustomerLoginView(LoginView):
    """Login: equipe vai para o painel, clientes para a lista de veículos."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        if self.request.user.is_staff:
            return reverse("core:dashboard")
        return super().get_default_redirect_url()


def register(request):
    if request.user.is_authenticated:
        return redirect("vehicles:list")
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Cadastro realizado! Você já está logado.")
        return redirect("vehicles:list")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    customer, _ = Customer.objects.get_or_create(user=request.user)
    user_form = UserProfileForm(request.POST or None, instance=request.user, prefix="user")
    customer_form = CustomerProfileForm(request.POST or None, instance=customer, prefix="customer")
    if request.method == "POST" and user_form.is_valid() and customer_form.is_valid():
        with transaction.atomic():
            user_form.save()
            customer_form.save()
        messages.success(request, "Dados atualizados com sucesso.")
        return redirect("accounts:profile")
    return render(
        request,
        "accounts/profile.html",
        {"user_form": user_form, "customer_form": customer_form},
    )
