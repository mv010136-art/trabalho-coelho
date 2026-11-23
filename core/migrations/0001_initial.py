from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="nome")),
                ("email", models.EmailField(max_length=254, verbose_name="e-mail")),
                ("message", models.TextField(verbose_name="mensagem")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="recebida em")),
            ],
            options={
                "verbose_name": "mensagem de contato",
                "verbose_name_plural": "mensagens de contato",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
