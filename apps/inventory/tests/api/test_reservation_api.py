import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.models import Reservation
from apps.inventory.services import ReservationService
from apps.inventory.tests.factories import StockFactory


pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

def test_availability_returns_stock_state(api_client):
    stock = StockFactory(
        quantity=10,
        reserved_quantity=3,
    )

    response = api_client.get(
        reverse(
            "inventory-api-v1:availability"
        ),
        {
            "product_id": stock.product_id,
            "warehouse_id": stock.warehouse_id,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.data["quantity"] == 10
    assert response.data["reserved_quantity"] == 3
    assert response.data["available_quantity"] == 7

def test_create_reservation_via_api(api_client):
    stock = StockFactory(
        quantity=10,
        reserved_quantity=0,
    )

    response = api_client.post(
        reverse(
            "inventory-api-v1:reservation-create"
        ),
        {
            "product_id": str(stock.product_id),
            "warehouse_id": str(stock.warehouse_id),
            "quantity": 3,
            "external_reference": "ORDER-001",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="KEY-001",
    )

    assert response.status_code == status.HTTP_201_CREATED

    assert response.data["status"] == Reservation.Status.ACTIVE
    assert response.data["quantity"] == 3

    stock.refresh_from_db()

    assert stock.quantity == 10
    assert stock.reserved_quantity == 3

def test_create_reservation_requires_idempotency_key(api_client):
    stock = StockFactory(
        quantity=10,
    )

    response = api_client.post(
        reverse(
            "inventory-api-v1:reservation-create"
        ),
        {
            "product_id": str(stock.product_id),
            "warehouse_id": str(stock.warehouse_id),
            "quantity": 1,
            "external_reference": "ORDER-001",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_create_reservation_returns_conflict_when_stock_is_insufficient(api_client):
    stock = StockFactory(
        quantity=2,
        reserved_quantity=2,
    )

    response = api_client.post(
        reverse(
            "inventory-api-v1:reservation-create"
        ),
        {
            "product_id": str(stock.product_id),
            "warehouse_id": str(stock.warehouse_id),
            "quantity": 1,
            "external_reference": "ORDER-001",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="KEY-001",
    )

    assert response.status_code == status.HTTP_409_CONFLICT

def test_confirm_reservation_via_api(api_client):
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

    response = api_client.post(
        reverse(
            "inventory-api-v1:reservation-confirm",
            kwargs={
                "reservation_id": reservation.id,
            },
        ),
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == Reservation.Status.CONFIRMED

    stock.refresh_from_db()

    assert stock.quantity == 7
    assert stock.reserved_quantity == 0

def test_cancel_reservation_via_api(api_client):
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

    response = api_client.post(
        reverse(
            "inventory-api-v1:reservation-cancel",
            kwargs={
                "reservation_id": reservation.id,
            },
        ),
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == Reservation.Status.CANCELLED

    stock.refresh_from_db()

    assert stock.quantity == 10
    assert stock.reserved_quantity == 0

def test_repeated_create_request_does_not_reserve_twice(api_client):
    stock = StockFactory(
        quantity=10,
    )

    url = reverse(
        "inventory-api-v1:reservation-create"
    )

    payload = {
        "product_id": str(stock.product_id),
        "warehouse_id": str(stock.warehouse_id),
        "quantity": 3,
        "external_reference": "ORDER-001",
    }

    first_response = api_client.post(
        url,
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY="KEY-001",
    )

    second_response = api_client.post(
        url,
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY="KEY-001",
    )

    stock.refresh_from_db()

    assert first_response.data["id"] == second_response.data["id"]

    assert stock.reserved_quantity == 3
    assert Reservation.objects.count() == 1