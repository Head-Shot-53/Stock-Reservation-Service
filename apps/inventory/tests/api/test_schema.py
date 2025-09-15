import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


def test_openapi_schema_is_available(api_client):
    response = api_client.get(
        reverse("api-schema"),
    )

    assert response.status_code == status.HTTP_200_OK

def test_swagger_ui_is_available(api_client):
    response = api_client.get(
        reverse("api-docs"),
    )

    assert response.status_code == status.HTTP_200_OK

def test_redoc_is_available(api_client):
    response = api_client.get(
        reverse("api-redoc"),
    )

    assert response.status_code == status.HTTP_200_OK

def test_openapi_schema_contains_reservation_endpoints(api_client):
    response = api_client.get(
        reverse("api-schema"),
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == status.HTTP_200_OK

    schema = response.json()

    paths = schema["paths"]

    assert "/api/v1/availability/" in paths
    assert "/api/v1/reservations/" in paths

    assert (
        "/api/v1/reservations/{reservation_id}/"
        in paths
    )

    assert (
        "/api/v1/reservations/"
        "{reservation_id}/confirm/"
        in paths
    )

    assert (
        "/api/v1/reservations/"
        "{reservation_id}/cancel/"
        in paths
    )

def test_create_reservation_schema_contains_idempotency_header(api_client):
    response = api_client.get(
        reverse("api-schema"),
        HTTP_ACCEPT="application/json",
    )

    schema = response.json()

    operation = schema["paths"][
        "/api/v1/reservations/"
    ]["post"]

    parameters = operation["parameters"]

    idempotency_parameter = next(
        parameter
        for parameter in parameters
        if parameter["name"] == "Idempotency-Key"
    )

    assert idempotency_parameter["in"] == "header"
    assert idempotency_parameter["required"] is True

def test_create_reservation_schema_documents_responses(api_client):
    response = api_client.get(
        reverse("api-schema"),
        HTTP_ACCEPT="application/json",
    )

    schema = response.json()

    responses = schema["paths"][
        "/api/v1/reservations/"
    ]["post"]["responses"]

    assert "201" in responses
    assert "400" in responses
    assert "404" in responses
    assert "409" in responses