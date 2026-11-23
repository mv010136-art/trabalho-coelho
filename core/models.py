from django.db import models


class ContactMessage(models.Model):
    """Mensagem enviada pelo formulário de contato (antes: PrivateMsg)."""

    name = models.CharField("nome", max_length=200)
    email = models.EmailField("e-mail")
    message = models.TextField("mensagem")
    created_at = models.DateTimeField("recebida em", auto_now_add=True)

    class Meta:
        verbose_name = "mensagem de contato"
        verbose_name_plural = "mensagens de contato"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
