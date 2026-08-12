from datetime import timedelta

import pytest
from django.utils import timezone

from apps.inventory.exceptions import (
    IdempotencyConflictError,
    InsufficientAvailableStockError,
    InvalidReservationQuantityError,
    ProductInactiveError,
    WarehouseInactiveError,
)
from apps.inventory.models import (
    Reservation,
    StockMovement,
)
from apps.inventory.services import ReservationService
from apps.inventory.tests.factories import StockFactory


pytestmark = pytest.mark.django_db

def test_create_reservation_creates_active_reservation():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=2,
    )

    before = timezone.now()

    reservation = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=3,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    assert reservation.status == Reservation.Status.ACTIVE
    assert reservation.quantity == 3
    assert reservation.product == stock.product
    assert reservation.warehouse == stock.warehouse
    assert reservation.external_reference == "ORDER-001"

    assert reservation.expires_at >= (
        before + timedelta(minutes=15)
    )

def test_create_reservation_increases_reserved_quantity():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=2,
    )

    ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=3,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    stock.refresh_from_db()

    assert stock.quantity == 10
    assert stock.reserved_quantity == 5
    assert stock.available_quantity == 5

def test_create_reservation_creates_stock_movement():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=2,
    )

    reservation = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=3,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    movement = StockMovement.objects.get(
        reservation=reservation,
    )

    assert movement.movement_type == (
        StockMovement.MovementType.RESERVATION_CREATED
    )
    assert movement.quantity == 3

    assert movement.quantity_before == 10
    assert movement.quantity_after == 10

    assert movement.reserved_before == 2
    assert movement.reserved_after == 5

def test_create_reservation_rejects_insufficient_stock():
    stock = StockFactory(
        quantity=5,
        reserved_quantity=4,
    )

    with pytest.raises(
        InsufficientAvailableStockError
    ):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=2,
            external_reference="ORDER-001",
            idempotency_key="KEY-001",
        )

    stock.refresh_from_db()

    assert stock.quantity == 5
    assert stock.reserved_quantity == 4

    assert Reservation.objects.count() == 0
    assert StockMovement.objects.count() == 0

def test_create_reservation_rejects_inactive_product():
    stock = StockFactory(
        quantity=10,
    )

    stock.product.is_active = False
    stock.product.save(
        update_fields=("is_active",)
    )

    with pytest.raises(ProductInactiveError):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=1,
            external_reference="ORDER-001",
            idempotency_key="KEY-001",
        )

def test_create_reservation_rejects_inactive_warehouse():
    stock = StockFactory(
        quantity=10,
    )

    stock.warehouse.is_active = False
    stock.warehouse.save(
        update_fields=("is_active",)
    )

    with pytest.raises(WarehouseInactiveError):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=1,
            external_reference="ORDER-001",
            idempotency_key="KEY-001",
        )


@pytest.mark.parametrize("quantity",[0, -1, -10,],)
def test_create_reservation_rejects_invalid_quantity(quantity,):
    stock = StockFactory(quantity=10,)

    with pytest.raises(
        InvalidReservationQuantityError
    ):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=quantity,
            external_reference="ORDER-001",
            idempotency_key="KEY-001",
        )

def test_repeated_idempotent_request_does_not_reserve_twice():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=0,
    )

    first = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=3,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    second = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=3,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    stock.refresh_from_db()

    assert first.id == second.id

    assert stock.reserved_quantity == 3

    assert Reservation.objects.count() == 1

    assert StockMovement.objects.filter(
        movement_type=(
            StockMovement.MovementType.RESERVATION_CREATED
        )
    ).count() == 1

def test_idempotency_key_cannot_be_reused_for_different_request():
    stock = StockFactory(
        quantity=10,
    )

    ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=2,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    with pytest.raises(IdempotencyConflictError):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=3,
            external_reference="ORDER-001",
            idempotency_key="KEY-001",
        )

    stock.refresh_from_db()

    assert stock.reserved_quantity == 2