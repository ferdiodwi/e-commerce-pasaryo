from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import ProductVariant


def validate_stock_adjustment(current_stock, adjustment):
    if isinstance(adjustment, bool) or not isinstance(adjustment, int):
        raise ValidationError(
            "Penyesuaian stok harus berupa bilangan bulat."
        )

    new_stock = current_stock + adjustment

    if new_stock < 0:
        raise ValidationError(
            f"Stok tidak cukup. Stok tersedia: {current_stock}."
        )

    return ProductVariant._meta.get_field("stock").clean(
        new_stock,
        None,
    )


@transaction.atomic
def save_product_variant(variant, *, adjustment=0):
    is_new = variant.pk is None
    current_stock = 0

    if not is_new:
        current = (
            ProductVariant.objects.select_for_update()
            .filter(pk=variant.pk)
            .first()
        )

        if current is None:
            raise ValidationError("Varian sudah dihapus.")

        current_stock = current.stock

    new_stock = validate_stock_adjustment(
        current_stock,
        adjustment,
    )

    variant.stock = new_stock if is_new else current_stock
    variant.full_clean()

    if is_new:
        variant.save()

    else:
        variant.save(
            update_fields=["product", "color_name", "sku"]
        )

        if adjustment:
            updated = ProductVariant.objects.filter(
                pk=variant.pk,
                stock__gte=max(0, -adjustment),
            ).update(
                stock=F("stock") + adjustment,
            )

            if updated != 1:
                raise ValidationError(
                    "Stok tidak cukup atau varian sudah berubah."
                )

        variant.refresh_from_db(fields=["stock"])

    variant._stock_before = current_stock

    return variant

