from django import forms
from django.core.exceptions import ValidationError

from .models import Order
from .services import validate_order_status


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            "status",
            "estimated_delivery_from",
            "estimated_delivery_to",
        )

    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get("status")

        if new_status is None:
            return cleaned_data

        current_order = None

        if self.instance.pk:
            current_order = (
                Order.objects.select_for_update()
                .filter(pk=self.instance.pk)
                .first()
            )

            if current_order is None:
                raise ValidationError("Pesanan sudah dihapus.")

        validate_order_status(current_order, new_status)

        return cleaned_data
