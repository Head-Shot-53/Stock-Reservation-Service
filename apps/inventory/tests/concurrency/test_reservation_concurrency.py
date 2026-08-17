from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Barrier

import pytest
from django.db import close_old_connections

from apps.inventory.exceptions import (
    InsufficientAvailableStockError,
    InvalidReservationStateError,
)
from apps.inventory.models import (
    Reservation,
    StockMovement,
)
from apps.inventory.services import ReservationService
from apps.inventory.tests.factories import StockFactory


@pytest.mark.django_db(transaction=True)
def test_only_one_concurrent_reservation_can_take_last_item():
    stock = StockFactory(
        quantity=1,
        reserved_quantity=0,
    )

    barrier = Barrier(2)
    results = Queue()

    def reserve_item(client_name: str) -> None:
        close_old_connections()

        try:
            barrier.wait()

            reservation = ReservationService.create_reservation(
                product_id=stock.product_id,
                warehouse_id=stock.warehouse_id,
                quantity=1,
                external_reference=f"ORDER-{client_name}",
                idempotency_key=f"KEY-{client_name}",
            )

            results.put(
                (
                    "success",
                    reservation.id,
                )
            )

        except InsufficientAvailableStockError:
            results.put(
                (
                    "insufficient_stock",
                    None,
                )
            )

        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                reserve_item,
                "A",
            ),
            executor.submit(
                reserve_item,
                "B",
            ),
        ]

        for future in futures:
            future.result(timeout=10)

    outcomes = [
        results.get_nowait(),
        results.get_nowait(),
    ]

    statuses = sorted(
        status
        for status, _ in outcomes
    )

    assert statuses == [
        "insufficient_stock",
        "success",
    ]

    stock.refresh_from_db()

    assert stock.quantity == 1
    assert stock.reserved_quantity == 1
    assert stock.available_quantity == 0

    assert Reservation.objects.filter(
        status=Reservation.Status.ACTIVE,
    ).count() == 1

    assert StockMovement.objects.filter(
        movement_type=(
            StockMovement.MovementType.RESERVATION_CREATED
        ),
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirm_does_not_deduct_stock_twice():
    stock = StockFactory(
        quantity=1,
        reserved_quantity=0,
    )

    reservation = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=1,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    barrier = Barrier(2)
    results = Queue()

    def confirm_reservation() -> None:
        close_old_connections()

        try:
            barrier.wait()

            result = ReservationService.confirm_reservation(
                reservation_id=reservation.id,
            )

            results.put(
                (
                    "success",
                    result.status,
                )
            )

        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(confirm_reservation),
            executor.submit(confirm_reservation),
        ]

        for future in futures:
            future.result(timeout=10)

    stock.refresh_from_db()
    reservation.refresh_from_db()

    assert reservation.status == Reservation.Status.CONFIRMED

    assert stock.quantity == 0
    assert stock.reserved_quantity == 0
    assert stock.available_quantity == 0

    assert StockMovement.objects.filter(
        reservation=reservation,
        movement_type=(
            StockMovement.MovementType.RESERVATION_CONFIRMED
        ),
    ).count() == 1

    assert results.qsize() == 2


@pytest.mark.django_db(transaction=True)
def test_confirm_and_cancel_cannot_both_win():
    stock = StockFactory(
        quantity=1,
        reserved_quantity=0,
    )

    reservation = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=1,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    barrier = Barrier(2)
    results = Queue()

    def confirm() -> None:
        close_old_connections()

        try:
            barrier.wait()

            ReservationService.confirm_reservation(
                reservation_id=reservation.id,
            )

            results.put("confirmed")

        except InvalidReservationStateError:
            results.put("confirm_rejected")

        finally:
            close_old_connections()

    def cancel() -> None:
        close_old_connections()

        try:
            barrier.wait()

            ReservationService.cancel_reservation(
                reservation_id=reservation.id,
            )

            results.put("cancelled")

        except InvalidReservationStateError:
            results.put("cancel_rejected")

        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(confirm),
            executor.submit(cancel),
        ]

        for future in futures:
            future.result(timeout=10)

    outcomes = {
        results.get_nowait(),
        results.get_nowait(),
    }

    reservation.refresh_from_db()
    stock.refresh_from_db()

    if reservation.status == Reservation.Status.CONFIRMED:
        assert outcomes == {
            "confirmed",
            "cancel_rejected",
        }

        assert stock.quantity == 0
        assert stock.reserved_quantity == 0

    elif reservation.status == Reservation.Status.CANCELLED:
        assert outcomes == {
            "cancelled",
            "confirm_rejected",
        }

        assert stock.quantity == 1
        assert stock.reserved_quantity == 0

    else:
        pytest.fail(
            f"Unexpected reservation status: {reservation.status}"
        )


@pytest.mark.django_db(transaction=True)
def test_concurrency_suite_uses_postgresql():
    from django.db import connection

    assert connection.vendor == "postgresql"