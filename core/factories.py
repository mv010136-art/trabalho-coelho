"""Funções auxiliares para criar dados nos testes."""
import datetime
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Customer
from reservations.models import Reservation
from vehicles.models import Vehicle

PASSWORD = "Senha-Forte-123"
_seq = count(1)


def day(offset=0):
    """Data local de hoje + ``offset`` dias."""
    return timezone.localdate() + datetime.timedelta(days=offset)


def make_user(username=None, staff=False, **extra):
    User = get_user_model()
    username = username or f"user{next(_seq)}"
    extra.setdefault("email", f"{username}@example.com")
    return User.objects.create_user(username=username, password=PASSWORD, is_staff=staff, **extra)


def make_customer(username=None, **extra):
    user = make_user(username, **extra)
    return Customer.objects.create(user=user, phone="(86) 99999-0000")


def make_vehicle(**overrides):
    n = next(_seq)
    data = {
        "name": f"Carro {n}",
        "brand": "Marca",
        "plate": f"TST{n % 10000:04d}",
        "seats": 5,
        "daily_rate": Decimal("100.00"),
        "description": "Veículo de teste",
        "is_active": True,
    }
    data.update(overrides)
    return Vehicle.objects.create(**data)


def make_reservation(customer, vehicle, start=1, end=4, status=Reservation.Status.CONFIRMED):
    """Cria uma reserva com datas relativas a hoje (start/end em dias)."""
    return Reservation.objects.create(
        customer=customer,
        vehicle=vehicle,
        start_date=day(start),
        end_date=day(end),
        status=status,
    )
