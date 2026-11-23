from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="category",
            field=models.CharField(
                choices=[
                    ("economy", "Econômico"),
                    ("sedan", "Sedã"),
                    ("suv", "SUV"),
                    ("van", "Van / Utilitário"),
                    ("premium", "Premium"),
                ],
                default="economy",
                max_length=12,
                verbose_name="categoria",
            ),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="transmission",
            field=models.CharField(
                choices=[("manual", "Manual"), ("automatic", "Automático")],
                default="manual",
                max_length=12,
                verbose_name="câmbio",
            ),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="fuel",
            field=models.CharField(
                choices=[
                    ("flex", "Flex"),
                    ("gasoline", "Gasolina"),
                    ("diesel", "Diesel"),
                    ("electric", "Elétrico"),
                    ("hybrid", "Híbrido"),
                ],
                default="flex",
                max_length=12,
                verbose_name="combustível",
            ),
        ),
    ]
