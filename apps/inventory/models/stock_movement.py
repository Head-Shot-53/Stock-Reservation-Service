import uuid

from django.db import models
from django.db.models import F, Q

from .stock import Stock


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        STOCK_INCREASE = "STOCK_INCREASE", "Stock increase"
        STOCK_DECREASE = "STOCK_DECREASE", "Stock decrease"
        RESERVATION_CREATED = (
            "RESERVATION_CREATED",
            "Reservation created",
        )
        RESERVATION_CONFIRMED = (
            "RESERVATION_CONFIRMED",
            "Reservation confirmed",
        )
        RESERVATION_CANCELLED = (
            "RESERVATION_CANCELLED",
            "Reservation cancelled",
        )
        RESERVATION_EXPIRED = (
            "RESERVATION_EXPIRED",
            "Reservation expired",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="movements",
    )

    movement_type = models.CharField(
        max_length=32,
        choices=MovementType.choices,
    )

    quantity = models.PositiveIntegerField()

    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()

    reserved_before = models.IntegerField()
    reserved_after = models.IntegerField()

    external_reference = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)

        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="inventory_movement_quantity_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(quantity_before__gte=0),
                name="inventory_movement_quantity_before_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(quantity_after__gte=0),
                name="inventory_movement_quantity_after_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(reserved_before__gte=0),
                name="inventory_movement_reserved_before_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(reserved_after__gte=0),
                name="inventory_movement_reserved_after_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(
                    reserved_before__lte=F("quantity_before"),
                ),
                name="inventory_movement_reserved_before_lte_quantity",
            ),
            models.CheckConstraint(
                condition=Q(
                    reserved_after__lte=F("quantity_after"),
                ),
                name="inventory_movement_reserved_after_lte_quantity",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.movement_type}: "
            f"{self.stock} ({self.quantity})"
        )