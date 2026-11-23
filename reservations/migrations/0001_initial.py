import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Reservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField(verbose_name="retirada")),
                ("end_date", models.DateField(verbose_name="devolução")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("confirmed", "Confirmada"),
                            ("cancelled", "Cancelada"),
                            ("completed", "Concluída"),
                        ],
                        default="confirmed",
                        max_length=12,
                        verbose_name="situação",
                    ),
                ),
                (
                    "daily_rate",
                    models.DecimalField(blank=True, decimal_places=2, editable=False, max_digits=8, null=True, verbose_name="diária (R$)"),
                ),
                (
                    "total_price",
                    models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=10, verbose_name="valor total (R$)"),
                ),
                ("notes", models.TextField(blank=True, verbose_name="observações")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizada em")),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservations",
                        to="accounts.customer",
                        verbose_name="cliente",
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservations",
                        to="vehicles.vehicle",
                        verbose_name="veículo",
                    ),
                ),
            ],
            options={
                "verbose_name": "reserva",
                "verbose_name_plural": "reservas",
                "ordering": ["-start_date", "-id"],
                "indexes": [
                    models.Index(fields=["vehicle", "start_date", "end_date"], name="res_vehicle_period_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("end_date__gt", models.F("start_date"))),
                        name="reservation_end_after_start",
                    ),
                ],
            },
        ),
    ]
