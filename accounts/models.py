from django.conf import settings
from django.db import models


class Customer(models.Model):
    """Perfil de cliente ligado ao usuário do Django (um-para-um)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer",
        verbose_name="usuário",
    )
    phone = models.CharField("telefone", max_length=20, blank=True)
    address = models.TextField("endereço", blank=True)
    driver_license = models.CharField("CNH", max_length=20, blank=True)
    created_at = models.DateTimeField("cadastrado em", auto_now_add=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["user__username"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.get_username()
