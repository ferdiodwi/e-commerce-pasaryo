from django import forms
from django.core.exceptions import ValidationError

from orders.models import Order

from .models import Payment


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        order = cleaned_data.get("order")

        if order is not None:
            locked_order = (
                Order.objects.select_for_update()
                .filter(pk=order.pk)
                .first()
            )

            if locked_order is None:
                raise ValidationError(
                    {"order": "Pesanan tidak ditemukan."}
                )

            cleaned_data["order"] = locked_order

        return cleaned_data