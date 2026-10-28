from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Order, OrderTracking


ALLOWED_TRANSITIONS = {
    Order.Status.TO_PAY: set(),
    Order.Status.PROCESSING: {Order.Status.SHIPPED},
    Order.Status.SHIPPED: set(),
    Order.Status.COMPLETED: set(),
    Order.Status.CANCELLED: set(),
}


def validate_order_status(order, new_status):
    if order is None:
        raise ValidationError(
            {
                "status": (
                    "Pesanan baru hanya dibuat melalui proses "
                    "checkout pembeli."
                )
            }
        )

    if new_status == order.status:
        return

    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise ValidationError(
            {"status": "Perubahan status tidak sesuai urutan pesanan."}
        )

    successful_payments = order.payments.filter(
        payment_status="SUCCESS",
    )

    if new_status == Order.Status.SHIPPED:
        if not successful_payments.filter(
            payment_amount=order.total_amount,
        ).exists():
            raise ValidationError(
                {
                    "status": (
                        "Pesanan harus memiliki pembayaran sukses "
                        "sesuai total."
                    )
                }
            )


@transaction.atomic
def sync_order_tracking(order):
    order = Order.objects.select_for_update().get(pk=order.pk)

    status_map = {
        Order.Status.TO_PAY: OrderTracking.StatusCode.ORDER_PLACED,
        Order.Status.PROCESSING: OrderTracking.StatusCode.PROCESSING,
        Order.Status.SHIPPED: OrderTracking.StatusCode.SHIPPED,
        Order.Status.COMPLETED: OrderTracking.StatusCode.DELIVERED,
        Order.Status.CANCELLED: OrderTracking.StatusCode.CANCELLED,
    }

    status_code = status_map[order.status]

    tracking = (
        order.trackings.filter(status_code=status_code)
        .order_by("pk")
        .first()
    )

    if tracking is None:
        tracking = OrderTracking(
            order=order,
            status_code=status_code,
        )

    if not tracking.is_completed:
        tracking.description = (
            tracking.description
            or f"Status pesanan: {order.get_status_display()}"
        )

        tracking.event_time = (
            order.created_at
            if order.status == Order.Status.TO_PAY
            else timezone.now()
        )

        tracking.is_completed = True
        tracking.full_clean()
        tracking.save()

    return tracking
