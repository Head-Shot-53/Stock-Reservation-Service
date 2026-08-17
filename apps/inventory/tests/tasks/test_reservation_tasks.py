from datetime import timedelta

import pytest
from django.utils import timezone

from apps.inventory.models import Reservation
from apps.inventory.services import ReservationService
from apps.inventory.tasks import expire_stale_reservations
from apps.inventory.tests.factories import StockFactory


pytestmark = pytest.mark.django_db


def create_expired_reservation(*,quantity: int = 2,stock_quantity: int = 10):
    stock = StockFactory(
        quantity=stock_quantity,
        reserved_quantity=0,
    )

    reservation = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=quantity,
        external_reference=f"ORDER-{stock.id}",
        idempotency_key=f"KEY-{stock.id}",
    )

    Reservation.objects.filter(
        id=reservation.id,
    ).update(
        expires_at=(
            timezone.now()
            - timedelta(seconds=1)
        )
    )

    reservation.refresh_from_db()

    return stock, reservation

def test_expire_stale_reservations_expires_active_reservation():
    stock, reservation = create_expired_reservation(
        quantity=3,
        stock_quantity=10,
    )

    processed = expire_stale_reservations(
        batch_size=100,
    )

    stock.refresh_from_db()
    reservation.refresh_from_db()

    assert processed == 1

    assert reservation.status == Reservation.Status.EXPIRED

    assert stock.quantity == 10
    assert stock.reserved_quantity == 0
    assert stock.available_quantity == 10

def test_expire_stale_reservations_ignores_future_reservations():
    stock = StockFactory(
        quantity=10,
    )

    reservation = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=3,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    processed = expire_stale_reservations(
        batch_size=100,
    )

    reservation.refresh_from_db()
    stock.refresh_from_db()

    assert processed == 0
    assert reservation.status == Reservation.Status.ACTIVE
    assert stock.reserved_quantity == 3

def test_expire_stale_reservations_respects_batch_size():
    for _ in range(3):
        create_expired_reservation()

    processed = expire_stale_reservations(
        batch_size=2,
    )

    assert processed == 2

    assert Reservation.objects.filter(
        status=Reservation.Status.EXPIRED,
    ).count() == 2

    assert Reservation.objects.filter(
        status=Reservation.Status.ACTIVE,
    ).count() == 1

def test_expire_stale_reservations_is_safe_to_run_again():
    _, reservation = create_expired_reservation()

    first_processed = expire_stale_reservations()
    second_processed = expire_stale_reservations()

    reservation.refresh_from_db()

    assert first_processed == 1
    assert second_processed == 0

    assert reservation.status == Reservation.Status.EXPIRED