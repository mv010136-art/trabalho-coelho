import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="telefone")),
                ("address", models.TextField(blank=True, verbose_name="endereço")),
                ("driver_license", models.CharField(blank=True, max_length=20, verbose_name="CNH")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="cadastrado em")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customer",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "cliente",
                "verbose_name_plural": "clientes",
                "ordering": ["user__username"],
            },
        ),
    ]
