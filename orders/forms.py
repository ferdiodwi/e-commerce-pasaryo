from django import forms
from django.core.exceptions import ValidationError
from django.db import connection

from .models import Order, OrderTracking
from .services import validate_order_status


# Form edit pesanan di admin
class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            "status",
            "estimated_delivery_from",
            "estimated_delivery_to",
        )

    # Validasi transisi status pesanan
    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get("status")

        if new_status is None:
            return cleaned_data

        current_order = None

        if self.instance.pk:
            qs = (
                Order.objects.select_for_update()
                if connection.in_atomic_block
                else Order.objects
            )
            current_order = qs.filter(pk=self.instance.pk).first()

            if current_order is None:
                raise ValidationError("Pesanan sudah dihapus.")

        validate_order_status(current_order, new_status)

        return cleaned_data


# Form pelacakan pesanan
class OrderTrackingAdminForm(forms.ModelForm):
    # Pilihan status yang boleh ditambah manual oleh admin
    ADMIN_CREATE_CHOICES = [
        (
            OrderTracking.StatusCode.PROCESSING,
            OrderTracking.StatusCode.PROCESSING.label,
        ),
        (
            OrderTracking.StatusCode.SHIPPED,
            OrderTracking.StatusCode.SHIPPED.label,
        ),
        (
            OrderTracking.StatusCode.IN_TRANSIT,
            OrderTracking.StatusCode.IN_TRANSIT.label,
        ),
        (
            OrderTracking.StatusCode.DELIVERED,
            OrderTracking.StatusCode.DELIVERED.label,
        ),
    ]

    class Meta:
        model = OrderTracking
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "status_code" not in self.fields:
            return

        # Kunci status jika edit tracking lama
        if self.instance and self.instance.pk:
            self.fields["status_code"].choices = [
                (
                    self.instance.status_code,
                    self.instance.get_status_code_display(),
                ),
            ]
        else:
            self.fields["status_code"].choices = self.ADMIN_CREATE_CHOICES
            self.fields["status_code"].initial = (
                OrderTracking.StatusCode.IN_TRANSIT
            )

    # Validasi riwayat pelacakan
    def clean(self):
        cleaned_data = super().clean()
        status_code = cleaned_data.get("status_code")
        is_completed = cleaned_data.get("is_completed")
        event_time = cleaned_data.get("event_time")

        # Validasi edit tracking lama
        if self.instance and self.instance.pk:
            previous = (
                OrderTracking.objects.filter(pk=self.instance.pk).first()
            )

            if previous is None:
                raise ValidationError("Riwayat pesanan sudah dihapus.")

            if (
                "order" in cleaned_data
                and cleaned_data["order"] is not None
                and cleaned_data["order"].pk != previous.order_id
            ):
                self.add_error(
                    "order",
                    "Pesanan pada riwayat pelacakan tidak dapat dipindahkan.",
                )

            if status_code and status_code != previous.status_code:
                self.add_error(
                    "status_code",
                    "Status pelacakan yang sudah dibuat tidak dapat diubah.",
                )

            # Tahap yang selesai tidak boleh dibatalkan atau diubah waktunya
            if previous.is_completed:
                if not is_completed:
                    self.add_error(
                        "is_completed",
                        "Tahap pelacakan yang sudah selesai tidak dapat dibatalkan.",
                    )
                prev_time = (
                    previous.event_time.replace(microsecond=0)
                    if previous.event_time is not None
                    else None
                )
                curr_time = (
                    event_time.replace(microsecond=0)
                    if event_time is not None
                    else None
                )
                if "event_time" in self.changed_data and curr_time != prev_time:
                    self.add_error(
                        "event_time",
                        "Waktu kejadian yang sudah selesai tidak dapat diubah.",
                    )
        # Validasi tambah tracking baru
        else:
            allowed_codes = {code for code, _ in self.ADMIN_CREATE_CHOICES}
            if status_code not in allowed_codes:
                self.add_error(
                    "status_code",
                    "Status pelacakan tidak diizinkan untuk penambahan manual.",
                )

            order = cleaned_data.get("order") or getattr(
                self.instance, "order", None
            )
            if order is not None and order.status in {
                Order.Status.TO_PAY,
                Order.Status.CANCELLED,
            }:
                raise ValidationError(
                    "Progres pengiriman hanya dapat ditambahkan pada "
                    "pesanan yang sedang diproses atau dikirim."
                )

        return cleaned_data
