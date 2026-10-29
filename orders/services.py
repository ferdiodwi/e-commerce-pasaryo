from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Order, OrderTracking


# Aturan transisi status pesanan
ALLOWED_TRANSITIONS = {
    Order.Status.TO_PAY: {
        Order.Status.PROCESSING,
        Order.Status.SHIPPED,
        Order.Status.CANCELLED,
    },
    Order.Status.PROCESSING: {
        Order.Status.SHIPPED,
        Order.Status.CANCELLED,
    },
    Order.Status.SHIPPED: {
        Order.Status.COMPLETED,
    },
    Order.Status.COMPLETED: set(),
    Order.Status.CANCELLED: set(),
}


# Validasi alur status pesanan
def validate_order_status(order, new_status):
    # Cegah buat order baru manual dari admin
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

    # Cek urutan transisi
    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise ValidationError(
            {"status": "Perubahan status tidak sesuai urutan pesanan."}
        )

    successful_payments = order.payments.filter(
        payment_status="SUCCESS",
    )

    # Wajib lunas sebelum diproses atau dikirim
    if new_status in {
        Order.Status.PROCESSING,
        Order.Status.SHIPPED,
        Order.Status.COMPLETED,
    }:
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

    # Cegah cancel jika sudah dibayar
    if new_status == Order.Status.CANCELLED and successful_payments.exists():
        raise ValidationError(
            {
                "status": (
                    "Pesanan sudah dibayar; pembatalan "
                    "memerlukan alur refund."
                )
            }
        )


# Sinkronkan status pesanan ke tracking
@transaction.atomic
def sync_order_tracking(order):
    order = Order.objects.select_for_update().get(pk=order.pk)

    # Pemetaan status order ke tracking
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

    # Buat tracking baru jika belum ada
    if tracking is None:
        tracking = OrderTracking(
            order=order,
            status_code=status_code,
        )

    # Tandai tahap ini selesai
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
