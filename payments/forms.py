from django import forms
from django.core.exceptions import ValidationError

from orders.models import Order

from .models import Payment


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = (
            "payment_status",
            "paid_at",
        )

    def clean(self):
        cleaned_data = super().clean()

        if self.instance.order_id:
            locked_order = (
                Order.objects.select_for_update()
                .filter(pk=self.instance.order_id)
                .first()
            )

            if locked_order is None:
                raise ValidationError("Pesanan tidak ditemukan.")

            self.instance.order = locked_order

        return cleaned_data
