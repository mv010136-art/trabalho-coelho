from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Customer
from vehicles.models import Vehicle

DEMO_VEHICLES = [
    {"plate": "DEM1A01", "category": "sedan", "transmission": "manual", "fuel": "flex", "name": "Honda Amaze", "brand": "Honda", "seats": 5, "daily_rate": "129.90",
     "description": "Sedã compacto, econômico, ideal para a cidade."},
    {"plate": "DEM1A02", "category": "economy", "transmission": "manual", "fuel": "flex", "name": "Fiat Mobi", "brand": "Fiat", "seats": 4, "daily_rate": "89.90",
     "description": "Hatch pequeno e fácil de estacionar."},
    {"plate": "DEM1A03", "category": "economy", "transmission": "manual", "fuel": "flex", "name": "Chevrolet Onix", "brand": "Chevrolet", "seats": 5, "daily_rate": "119.90",
     "description": "Hatch com ótimo custo-benefício e ar-condicionado."},
    {"plate": "DEM1A04", "category": "sedan", "transmission": "automatic", "fuel": "hybrid", "name": "Toyota Corolla", "brand": "Toyota", "seats": 5, "daily_rate": "219.90",
     "description": "Sedã médio confortável para viagens."},
    {"plate": "DEM1A05", "category": "suv", "transmission": "automatic", "fuel": "flex", "name": "Jeep Compass", "brand": "Jeep", "seats": 5, "daily_rate": "289.90",
     "description": "SUV espaçoso para estrada e terrenos irregulares."},
    {"plate": "DEM1A06", "category": "van", "transmission": "manual", "fuel": "diesel", "name": "Renault Master", "brand": "Renault", "seats": 15, "daily_rate": "429.90",
     "description": "Van para grupos grandes e excursões."},
]


class Command(BaseCommand):
    help = "Cria veículos de demonstração (e, opcionalmente, um cliente de demonstração)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--demo-customer",
            action="store_true",
            help="Também cria o usuário cliente_demo (senha: demo12345) — apenas para testes locais.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for data in DEMO_VEHICLES:
            defaults = {**data, "daily_rate": Decimal(data["daily_rate"])}
            plate = defaults.pop("plate")
            _, was_created = Vehicle.objects.get_or_create(plate=plate, defaults=defaults)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f"{created} veículo(s) de demonstração criado(s); {len(DEMO_VEHICLES) - created} já existiam."
        ))

        if options["demo_customer"]:
            User = get_user_model()
            user, user_created = User.objects.get_or_create(
                username="cliente_demo",
                defaults={"first_name": "Cliente", "last_name": "Demo", "email": "cliente.demo@example.com"},
            )
            if user_created:
                user.set_password("demo12345")
                user.save()
            Customer.objects.get_or_create(user=user, defaults={"phone": "(86) 99999-0000"})
            self.stdout.write(self.style.WARNING(
                "Cliente de demonstração: usuário 'cliente_demo' / senha 'demo12345' "
                "(NÃO use em produção)."
                if user_created else "Usuário cliente_demo já existia (senha inalterada)."
            ))
