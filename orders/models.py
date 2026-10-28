from decimal import Decimal

from django.core.validators import MinValueValidator
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