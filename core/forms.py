from django import forms

from .models import ContactMessage


class BootstrapFormMixin:
    """Aplica as classes do Bootstrap 3 aos widgets do formulário."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.ClearableFileInput)):
                continue
            css = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{css} form-control".strip()


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
