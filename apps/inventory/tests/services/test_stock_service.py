import pytest

from apps.inventory.exceptions import (
    InsufficientAvailableStockError,
    InvalidStockQuantityError,
    StockNotFoundError,
)
from apps.inventory.models import StockMovement
from apps.inventory.services import StockService
from apps.inventory.tests.factories import StockFactory

from unittest.mock import patch


pytestmark = pytest.mark.django_db


def test_increase_stock_changes_quantity():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=2,
    )

    StockService.increase_stock(
        stock_id=stock.id,
        quantity=5,
    )

    stock.refresh_from_db()

    assert stock.quantity == 15
    assert stock.reserved_quantity == 2
    assert stock.available_quantity == 13


def test_increase_stock_creates_movement():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=2,
    )

    StockService.increase_stock(
        stock_id=stock.id,
        quantity=5,
        external_reference="delivery-001",
    )

    movement = StockMovement.objects.get(
        stock=stock,
    )

    assert movement.movement_type == (
        StockMovement.MovementType.STOCK_INCREASE
    )
    assert movement.quantity == 5
    assert movement.quantity_before == 10
    assert movement.quantity_after == 15
    assert movement.reserved_before == 2
    assert movement.reserved_after == 2
    assert movement.external_reference == "delivery-001"


def test_decrease_stock_changes_quantity():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=3,
    )

    StockService.decrease_stock(
        stock_id=stock.id,
        quantity=4,
    )

    stock.refresh_from_db()

    assert stock.quantity == 6
    assert stock.reserved_quantity == 3
    assert stock.available_quantity == 3


def test_decrease_stock_can_use_all_available_quantity():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=3,
    )

    StockService.decrease_stock(
        stock_id=stock.id,
        quantity=7,
    )

    stock.refresh_from_db()

    assert stock.quantity == 3
    assert stock.reserved_quantity == 3
    assert stock.available_quantity == 0


def test_decrease_stock_cannot_touch_reserved_stock():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=3,
    )

    with pytest.raises(
        InsufficientAvailableStockError
    ):
        StockService.decrease_stock(
            stock_id=stock.id,
            quantity=8,
        )

    stock.refresh_from_db()

    assert stock.quantity == 10
    assert stock.reserved_quantity == 3
    assert StockMovement.objects.count() == 0


@pytest.mark.parametrize(
    "quantity",
    [
        0,
        -1,
        -10,
    ],
)
def test_increase_stock_rejects_invalid_quantity(quantity):
    stock = StockFactory()

    with pytest.raises(
        InvalidStockQuantityError
    ):
        StockService.increase_stock(
            stock_id=stock.id,
            quantity=quantity,
        )


@pytest.mark.parametrize(
    "quantity",
    [
        0,
        -1,
        -10,
    ],
)
def test_decrease_stock_rejects_invalid_quantity(quantity):
    stock = StockFactory(
        quantity=10,
    )

    with pytest.raises(
        InvalidStockQuantityError
    ):
        StockService.decrease_stock(
            stock_id=stock.id,
            quantity=quantity,
        )


def test_increase_stock_raises_when_stock_does_not_exist():
    import uuid

    with pytest.raises(
        StockNotFoundError
    ):
        StockService.increase_stock(
            stock_id=uuid.uuid4(),
            quantity=10,
        )


def test_stock_change_is_rolled_back_when_movement_creation_fails():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=0,
    )

    with patch.object(
        StockMovement.objects,
        "create",
        side_effect=RuntimeError("Movement creation failed"),
    ):
        with pytest.raises(RuntimeError):
            StockService.increase_stock(
                stock_id=stock.id,
                quantity=5,
            )

    stock.refresh_from_db()

    assert stock.quantity == 10
    assert StockMovement.objects.count() == 0