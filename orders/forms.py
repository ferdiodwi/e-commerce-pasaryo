from django import forms
from django.core.exceptions import ValidationError

from .models import Order, OrderTracking
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


class OrderTrackingAdminForm(forms.ModelForm):
    class Meta:
        model = OrderTracking
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "status_code" not in self.fields:
            return

        if self.instance and self.instance.pk:
            self.fields["status_code"].choices = [
                (
                    self.instance.status_code,
                    self.instance.get_status_code_display(),
                ),
            ]
        else:
            self.fields["status_code"].choices = [
                (
                    OrderTracking.StatusCode.IN_TRANSIT,
                    OrderTracking.StatusCode.IN_TRANSIT.label,
                ),
            ]
            self.fields["status_code"].initial = (
                OrderTracking.StatusCode.IN_TRANSIT
            )

    def clean(self):
        cleaned_data = super().clean()
        status_code = cleaned_data.get("status_code")
        is_completed = cleaned_data.get("is_completed")
        event_time = cleaned_data.get("event_time")

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

            if previous.is_completed:
                if not is_completed:
                    self.add_error(
                        "is_completed",
                        "Tahap pelacakan yang sudah selesai tidak dapat dibatalkan.",
                    )
                if event_time != previous.event_time:
                    self.add_error(
                        "event_time",
                        "Waktu kejadian yang sudah selesai tidak dapat diubah.",
                    )
        else:
            if status_code != OrderTracking.StatusCode.IN_TRANSIT:
                self.add_error(
                    "status_code",
                    (
                        "Penambahan manual oleh admin hanya untuk "
                        "progres pengiriman (In Transit)."
                    ),
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
