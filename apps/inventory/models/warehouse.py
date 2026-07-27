from django.db import models
from django.db.models.functions import Lower

from .base import UUIDTimestampedModel


class Warehouse(UUIDTimestampedModel):
    code = models.CharField(
        max_length=32,
    )
    name = models.CharField(
        max_length=255,
    )
    address = models.CharField(
        max_length=500,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                Lower("code"),
                name="inventory_warehouse_code_ci_unique",
                violation_error_code="duplicate_warehouse_code",
                violation_error_message=(
                    "A warehouse with this code already exists."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"