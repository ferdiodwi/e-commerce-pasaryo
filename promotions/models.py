from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from django.core.validators import MaxValueValidator, MinValueValidator

class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "Persentase"
    FIXED = "fixed", "Fixed"


class Event(models.Model):
    name = models.CharField(max_length=150)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    products = models.ManyToManyField(
        "catalog.Product",
        through="EventProduct",
        related_name="events",
    )

    class Meta:
        db_table = "event"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        errors = {}

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            errors["end_date"] = (
                "Tanggal akhir harus lebih besar dari tanggal mulai."
            )

        if (
            self.discount_type == DiscountType.PERCENTAGE
            and self.discount_value is not None
            and self.discount_value > 100
        ):
            errors["discount_value"] = "Persentase maksimal 100."

        if errors:
            raise ValidationError(errors)


class EventProduct(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_products",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="event_products",
    )

    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
        null=True,
        blank=True,
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "event_product"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "product"],
                name="unique_event_product",
            ),
        ]

    def clean(self):
        super().clean()

        has_type = bool(self.discount_type)
        has_value = self.discount_value is not None

        if has_type != has_value:
            raise ValidationError(
                "Isi jenis dan nilai diskon bersamaan, "
                "atau kosongkan keduanya untuk mengikuti event."
            )

        if (
            self.discount_type == DiscountType.PERCENTAGE
            and self.discount_value is not None
            and self.discount_value > 100
        ):
            raise ValidationError(
                {"discount_value": "Persentase maksimal 100."}
            )



class Discount(models.Model):
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="discounts",
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    discount_value = models.DecimalField(
        verbose_name="Diskon (%)",
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Contoh: isi 20 untuk diskon 20%.",
    )

    class Meta:
        db_table = "discount"

    def __str__(self):
        return f"{self.product} - {self.discount_value}"

    def clean(self):
        super().clean()

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            raise ValidationError(
                {
                    "end_date": (
                        "Tanggal akhir harus lebih besar dari tanggal mulai."
                    )
                }
            )


class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)

    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    max_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    quota_total = models.PositiveIntegerField()
    quota_per_user = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "promo_codes"

    def __str__(self):
        return self.code

    def clean(self):
        super().clean()

        if self.code:
            self.code = self.code.strip().upper()

        if (
            self.discount_type == DiscountType.PERCENTAGE
            and self.discount_value is not None
            and self.discount_value > 100
        ):
            raise ValidationError(
                {"discount_value": "Persentase maksimal 100."}
            )