from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


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

        if self.payment_status == self.Status.SUCCESS:
            if self.paid_at is None:
                raise ValidationError(
                    {
                        "paid_at": (
                            "Waktu pembayaran wajib diisi "
                            "untuk status Success."
                        )
                    }
                )

        elif self.paid_at is not None:
            raise ValidationError(
                {
                    "paid_at": (
                        "Waktu pembayaran hanya diisi "
                        "untuk status Success."
                    )
                }
            )