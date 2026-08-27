import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.models import Reservation
from apps.inventory.services import ReservationService
from apps.inventory.tests.factories import StockFactory

import uuid


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
            "inventory-api-v1:reservation-list-create"
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
            "inventory-api-v1:reservation-list-create"
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
            "inventory-api-v1:reservation-list-create"
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
        "inventory-api-v1:reservation-list-create"
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

def test_list_reservations(api_client):
    stock = StockFactory(
        quantity=10,
    )

    first = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=1,
        external_reference="ORDER-001",
        idempotency_key="KEY-001",
    )

    second = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=1,
        external_reference="ORDER-002",
        idempotency_key="KEY-002",
    )

    response = api_client.get(
        reverse(
            "inventory-api-v1:reservation-list-create"
        )
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.data["count"] == 2
    assert len(response.data["results"]) == 2

    returned_ids = {
        item["id"]
        for item in response.data["results"]
    }

    assert str(first.id) in returned_ids
    assert str(second.id) in returned_ids

def test_list_reservations_can_filter_by_status(api_client,):
    stock = StockFactory(
        quantity=10,
    )

    active = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=1,
        external_reference="ORDER-ACTIVE",
        idempotency_key="KEY-ACTIVE",
    )

    confirmed = ReservationService.create_reservation(
        product_id=stock.product_id,
        warehouse_id=stock.warehouse_id,
        quantity=1,
        external_reference="ORDER-CONFIRMED",
        idempotency_key="KEY-CONFIRMED",
    )

    ReservationService.confirm_reservation(
        reservation_id=confirmed.id,
    )

    response = api_client.get(
        reverse(
            "inventory-api-v1:reservation-list-create"
        ),
        {
            "status": Reservation.Status.ACTIVE,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(active.id)

def test_reservation_list_is_paginated(api_client):
    stock = StockFactory(
        quantity=100,
    )

    for number in range(25):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=1,
            external_reference=f"ORDER-{number}",
            idempotency_key=f"KEY-{number}",
        )

    response = api_client.get(
        reverse(
            "inventory-api-v1:reservation-list-create"
        )
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.data["count"] == 25
    assert len(response.data["results"]) == 20
    assert response.data["next"] is not None
    assert response.data["previous"] is None

def test_reservation_list_supports_page_size(api_client):
    stock = StockFactory(
        quantity=10,
    )

    for number in range(5):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=1,
            external_reference=f"ORDER-{number}",
            idempotency_key=f"KEY-{number}",
        )

    response = api_client.get(
        reverse(
            "inventory-api-v1:reservation-list-create"
        ),
        {
            "page_size": 2,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 5
    assert len(response.data["results"]) == 2

def test_validation_errors_use_standard_error_format(api_client):
    response = api_client.post(
        reverse(
            "inventory-api-v1:reservation-list-create"
        ),
        {
            "quantity": 0,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert "error" in response.data
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["message"] == (
        "Request validation failed."
    )

    assert "details" in response.data["error"]

def test_insufficient_stock_uses_standard_error_format(api_client):
    stock = StockFactory(
        quantity=1,
        reserved_quantity=1,
    )

    response = api_client.post(
        reverse(
            "inventory-api-v1:reservation-list-create"
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

    assert response.data == {
        "error": {
            "code": "insufficient_available_stock",
            "message": "Not enough available stock.",
            "details": {},
        }
    }

def test_missing_reservation_uses_standard_error_format(api_client):
    reservation_id = uuid.uuid4()

    response = api_client.get(
        reverse(
            "inventory-api-v1:reservation-detail",
            kwargs={
                "reservation_id": reservation_id,
            },
        )
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert response.data["error"]["code"] == (
        "reservation_not_found"
    )

    assert response.data["error"]["details"] == {}

def test_reservation_list_does_not_create_n_plus_one_queries(api_client,django_assert_num_queries):
    stock = StockFactory(
        quantity=10,
    )

    for number in range(5):
        ReservationService.create_reservation(
            product_id=stock.product_id,
            warehouse_id=stock.warehouse_id,
            quantity=1,
            external_reference=f"ORDER-{number}",
            idempotency_key=f"KEY-{number}",
        )

    with django_assert_num_queries(2):
        response = api_client.get(
            reverse(
                "inventory-api-v1:reservation-list-create"
            )
        )

    assert response.status_code == status.HTTP_200_OK