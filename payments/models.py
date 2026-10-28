from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from orders.models import Order

class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)

    channel_provider = models.CharField(max_length=100)

    service_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "payment_methods"
        ordering = ["name", "id"]

    def __str__(self):
        return f"{self.name} - {self.channel_provider}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
    )

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    payment_reference = models.CharField(
        max_length=100,
        unique=True,
    )

    payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
    )

    payment_status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    payment_url = models.URLField(
        max_length=500,
        blank=True,
    )

    class Meta:
        db_table = "payments"
        ordering = ["-id"]

    def __str__(self):
        return self.payment_reference

    def clean(self):
        super().clean()
        errors = {}

        previous = None
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()

        if previous and self.order_id != previous.order_id:
            errors["order"] = (
                "Pesanan pada pembayaran tersimpan tidak dapat dipindahkan. "
                "Buat catatan pembayaran baru."
            )

        already_final = (
            previous is not None
            and previous.payment_status != self.Status.PENDING
        )

        if already_final:
            protected_fields = (
                "payment_method",
                "payment_reference",
                "payment_amount",
                "payment_status",
                "paid_at",
            )

            error_message = (
                "Data konfirmasi pembayaran sukses tidak dapat diubah."
                if previous.payment_status == self.Status.SUCCESS
                else (
                    "Pembayaran yang sudah berakhir "
                    "(Failed/Expired) tidak dapat diubah lagi."
                )
            )

            for name in protected_fields:
                attname = self._meta.get_field(name).attname

                if getattr(self, attname) != getattr(previous, attname):
                    errors[name] = error_message

        if self.payment_status == self.Status.SUCCESS:
            if self.paid_at is None:
                errors["paid_at"] = (
                    "Waktu pembayaran wajib diisi untuk status Success."
                )

            if self.order_id and not already_final:
                order = Order.objects.filter(pk=self.order_id).first()

                if order is not None:
                    if order.status == Order.Status.CANCELLED:
                        errors["order"] = (
                            "Pesanan yang dibatalkan tidak dapat dikonfirmasi."
                        )

                    if (
                        self.payment_amount is not None
                        and self.payment_amount != order.total_amount
                    ):
                        errors["payment_amount"] = (
                            "Nominal pembayaran harus sama dengan total pesanan."
                        )

                    other_success = type(self).objects.filter(
                        order_id=self.order_id,
                        payment_status=self.Status.SUCCESS,
                    ).exclude(pk=self.pk)

                    if other_success.exists():
                        errors["payment_status"] = (
                            "Pesanan ini sudah memiliki pembayaran sukses."
                        )

        elif self.paid_at is not None:
            errors["paid_at"] = (
                "Waktu pembayaran hanya diisi untuk status Success."
            )

        if errors:
            raise ValidationError(errors)