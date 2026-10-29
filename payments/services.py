from django.core.exceptions import ValidationError
from django.db import transaction

from orders.models import Order, OrderTracking

from .models import Payment

from orders.services import sync_order_tracking


# Simpan pembayaran & update pesanan secara atomik
@transaction.atomic
def save_payment(payment):
    # Lock Order dan Payment
    order = (
        Order.objects.select_for_update()
        .filter(pk=payment.order_id)
        .first()
    )

    if order is None:
        raise ValidationError({"order": "Pesanan tidak ditemukan."})

    if payment.pk:
        existing = (
            Payment.objects.select_for_update()
            .filter(pk=payment.pk)
            .first()
        )

        if existing is None:
            raise ValidationError("Catatan pembayaran sudah dihapus.")

    payment.order = order
    payment.full_clean()
    payment.save()

    if payment.payment_status != Payment.Status.SUCCESS:
        return payment

    # Otomatis ubah status pesanan ke Processing
    if order.status == Order.Status.TO_PAY:
        order.status = Order.Status.PROCESSING
        order.save(update_fields=["status"])
        sync_order_tracking(order)

    # Catat riwayat konfirmasi pembayaran
    tracking = (
        OrderTracking.objects.filter(
            order=order,
            status_code=OrderTracking.StatusCode.PAYMENT_CONFIRMED,
        )
        .order_by("pk")
        .first()
    )

    if tracking is None:
        tracking = OrderTracking(
            order=order,
            status_code=OrderTracking.StatusCode.PAYMENT_CONFIRMED,
        )

    if not tracking.is_completed:
        tracking.description = (
            f"Pembayaran dikonfirmasi: {payment.payment_reference}"
        )
        tracking.event_time = payment.paid_at
        tracking.is_completed = True

        tracking.full_clean()
        tracking.save()

    return payment
