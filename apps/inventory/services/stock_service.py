import uuid

from django.db import transaction

from apps.inventory.exceptions import (
    InsufficientAvailableStockError,
    InvalidStockQuantityError,
    StockNotFoundError,
)
from apps.inventory.models import Stock, StockMovement


class StockService:
    @staticmethod
    def increase_stock(*,stock_id: uuid.UUID,quantity: int,external_reference: str = "") -> Stock:
        if quantity <= 0:
            raise InvalidStockQuantityError(
                "Quantity must be greater than zero."
            )

        with transaction.atomic():
            try:
                stock = (
                    Stock.objects
                    .select_for_update()
                    .select_related(
                        "product",
                        "warehouse",
                    )
                    .get(id=stock_id)
                )
            except Stock.DoesNotExist as exc:
                raise StockNotFoundError(
                    f"Stock {stock_id} does not exist."
                ) from exc

            quantity_before = stock.quantity
            reserved_before = stock.reserved_quantity

            stock.quantity += quantity

            stock.save(
                update_fields=(
                    "quantity",
                    "updated_at",
                )
            )

            StockMovement.objects.create(
                stock=stock,
                movement_type=(
                    StockMovement.MovementType.STOCK_INCREASE
                ),
                quantity=quantity,
                quantity_before=quantity_before,
                quantity_after=stock.quantity,
                reserved_before=reserved_before,
                reserved_after=stock.reserved_quantity,
                external_reference=external_reference,
            )

            return stock

    @staticmethod
    def decrease_stock(*,stock_id: uuid.UUID,quantity: int,external_reference: str = "",) -> Stock:
        if quantity <= 0:
            raise InvalidStockQuantityError(
                "Quantity must be greater than zero."
            )

        with transaction.atomic():
            try:
                stock = (
                    Stock.objects
                    .select_for_update()
                    .select_related(
                        "product",
                        "warehouse",
                    )
                    .get(id=stock_id)
                )
            except Stock.DoesNotExist as exc:
                raise StockNotFoundError(
                    f"Stock {stock_id} does not exist."
                ) from exc

            if quantity > stock.available_quantity:
                raise InsufficientAvailableStockError(
                    "Cannot decrease stock below reserved quantity."
                )

            quantity_before = stock.quantity
            reserved_before = stock.reserved_quantity

            stock.quantity -= quantity

            stock.save(
                update_fields=(
                    "quantity",
                    "updated_at",
                )
            )

            StockMovement.objects.create(
                stock=stock,
                movement_type=(
                    StockMovement.MovementType.STOCK_DECREASE
                ),
                quantity=quantity,
                quantity_before=quantity_before,
                quantity_after=stock.quantity,
                reserved_before=reserved_before,
                reserved_after=stock.reserved_quantity,
                external_reference=external_reference,
            )

            return stock