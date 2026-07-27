from django.db import models
from django.db.models.functions import Lower

from .base import UUIDTimestampedModel


class Product(UUIDTimestampedModel):
    sku = models.CharField(
        max_length=64,
    )
    name = models.CharField(
        max_length=255,
    )
    description = models.TextField(
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ("sku",)
        constraints = [
            models.UniqueConstraint(
                Lower("sku"),
                name="inventory_product_sku_ci_unique",
                violation_error_code="duplicate_sku",
                violation_error_message=(
                    "A product with this SKU already exists."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"