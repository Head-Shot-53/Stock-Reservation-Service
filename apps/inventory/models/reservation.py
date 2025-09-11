import uuid

from django.db import models
from django.db.models import Q


class Reservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    warehouse = models.ForeignKey(
        "inventory.Warehouse",
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    quantity = models.PositiveIntegerField()

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    external_reference = models.CharField(
        max_length=255,
        db_index=True,
    )

    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
    )

    expires_at = models.DateTimeField(
        db_index=True,
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    expired_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)

        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="inventory_reservation_quantity_gt_0",
            ),
        ]

        indexes = [
            models.Index(
                fields=(
                    "status",
                    "expires_at",
                ),
                name="inv_res_status_expires_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.external_reference} — "
            f"{self.product.sku} x{self.quantity}"
        )