from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    estimated_days = models.CharField(max_length=20)

    base_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "shipping_methods"

    def __str__(self):
        return self.name


def generate_order_number():
    return f"ORD-{uuid4().hex.upper()}"


class Order(models.Model):
    class Status(models.TextChoices):
        TO_PAY = "to_pay", "To Pay"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    order_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_order_number,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    shipping_method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    promo_code = models.ForeignKey(
        "promotions.PromoCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    shipping_address_snapshot = models.TextField()

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    shipping_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    service_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TO_PAY,
    )
    estimated_delivery_from = models.DateField(null=True, blank=True)
    estimated_delivery_to = models.DateField(null=True, blank=True)
    payment_due_at = models.DateTimeField(null=True, blank=True)
    checkout_key = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
    )
    checkout_payload = models.JSONField(
        default=dict,
        blank=True,
        editable=False,
    )
    stock_deducted = models.BooleanField(
        default=False,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "checkout_key"],
                name="unique_checkout_key_per_user",
            ),
        ]

    def __str__(self):
        return self.order_number

    def clean(self):
        super().clean()

        if (
            self.estimated_delivery_from
            and self.estimated_delivery_to
            and self.estimated_delivery_to < self.estimated_delivery_from
        ):
            raise ValidationError(
                {
                    "estimated_delivery_to": (
                        "Tanggal akhir estimasi tidak boleh lebih awal."
                    )
                }
            )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product_variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    product_name_snapshot = models.CharField(max_length=200)
    variant_name_snapshot = models.CharField(max_length=100)
    sku_snapshot = models.CharField(max_length=64)

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    price_at_purchase = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return (
            f"{self.order.order_number} | "
            f"Item #{self.pk} | "
            f"{self.product_name_snapshot}"
        )


class OrderTracking(models.Model):
    class StatusCode(models.TextChoices):
        ORDER_PLACED = "order_placed", "Order Placed"
        PAYMENT_CONFIRMED = "payment_confirmed", "Payment Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        IN_TRANSIT = "in_transit", "In Transit"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="trackings",
    )

    status_code = models.CharField(
        max_length=30,
        choices=StatusCode.choices,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    event_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Waktu kejadian benar-benar terjadi.",
    )

    expected_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Perkiraan waktu kejadian, jika ada.",
    )

    is_completed = models.BooleanField(
        default=False,
        help_text="Centang jika tahap ini sudah terjadi.",
    )

    class Meta:
        db_table = "order_trackings"
        ordering = ["event_time", "id"]
        verbose_name = "riwayat pesanan"
        verbose_name_plural = "riwayat pesanan"

    def __str__(self):
        return f"Order #{self.order_id} - {self.get_status_code_display()}"

    def clean(self):
        super().clean()

        if self.is_completed and self.event_time is None:
            raise ValidationError(
                {
                    "event_time": (
                        "Waktu kejadian wajib diisi jika tahap sudah terjadi."
                    )
                }
            )



class Review(models.Model):
    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="review",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        help_text="Isi rating dari 1 sampai 5.",
    )

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Review item #{self.order_item_id} - {self.rating}/5"