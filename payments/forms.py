from django import forms
from django.core.exceptions import ValidationError
from django.db import connection

from orders.models import Order

from .models import Payment


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        if self.instance.order_id:
            qs = (
                Order.objects.select_for_update()
                if connection.in_atomic_block
                else Order.objects
            )
            locked_order = qs.filter(pk=self.instance.order_id).first()

            if locked_order is None:
                raise ValidationError("Pesanan tidak ditemukan.")

            self.instance.order = locked_order

        return cleaned_data
