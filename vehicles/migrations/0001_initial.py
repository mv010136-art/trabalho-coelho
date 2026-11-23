import decimal

import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(blank=True, upload_to="vehicles/%Y/%m/", verbose_name="foto")),
                ("name", models.CharField(max_length=100, verbose_name="nome do veículo")),
                ("brand", models.CharField(max_length=100, verbose_name="marca")),
                ("plate", models.CharField(max_length=8, unique=True, verbose_name="placa")),
                (
                    "seats",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(60),
                        ],
                        verbose_name="número de lugares",
                    ),
                ),
                (
                    "daily_rate",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))],
                        verbose_name="diária (R$)",
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="descrição")),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Desmarque para retirar o veículo da locação (manutenção, venda etc.).",
                        verbose_name="ativo na frota",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="cadastrado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                (
                    "likes",
                    models.ManyToManyField(
                        blank=True,
                        related_name="liked_vehicles",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="curtidas",
                    ),
                ),
            ],
            options={
                "verbose_name": "veículo",
                "verbose_name_plural": "veículos",
                "ordering": ["name", "id"],
            },
        ),
    ]
