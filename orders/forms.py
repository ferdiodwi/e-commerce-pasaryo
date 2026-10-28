from decimal import Decimal

from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet


class OrderItemInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        subtotal = Decimal("0.00")
        item_count = 0

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            item = form.instance
            variant = item.product_variant

            if variant is None and not item.pk:
                raise ValidationError(
                    "Pilih varian untuk setiap item baru."
                )

            if variant is not None and (
                not item.pk or "product_variant" in form.changed_data
            ):
                item.product_name_snapshot = variant.product.name
                item.variant_name_snapshot = variant.color_name
                item.sku_snapshot = variant.sku
                item.price_at_purchase = variant.product.price

            try:
                item.full_clean(exclude={"order"})
            except ValidationError as error:
                raise ValidationError(
                    "Item pesanan tidak valid: "
                    + " ".join(error.messages)
                ) from error

            subtotal += item.quantity * item.price_at_purchase
            item_count += 1

        if item_count == 0:
            raise ValidationError(
                "Pesanan harus memiliki minimal satu item."
            )

        order = self.instance
        total = (
            subtotal
            + order.shipping_fee
            + order.service_fee
            - order.discount_amount
        )

        try:
            order.subtotal = order._meta.get_field("subtotal").clean(
                subtotal, order,
            )
            order.total_amount = order._meta.get_field(
                "total_amount"
            ).clean(total, order)

        except ValidationError as error:
            raise ValidationError(
                "Perhitungan pesanan tidak valid: "
                + " ".join(error.messages)
            ) from error