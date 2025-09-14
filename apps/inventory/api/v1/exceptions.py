from rest_framework.exceptions import (
    APIException,
    NotFound,
    ValidationError,
)

from apps.inventory.exceptions import (
    IdempotencyConflictError,
    InsufficientAvailableStockError,
    InvalidReservationQuantityError,
    InvalidReservationStateError,
    InvalidReservationTTLError,
    ProductInactiveError,
    ReservationExpiredError,
    ReservationNotExpiredError,
    ReservationNotFoundError,
    StockNotFoundError,
    WarehouseInactiveError,
)


class Conflict(APIException):
    status_code = 409
    default_detail = (
        "The request conflicts with "
        "the current resource state."
    )
    default_code = "conflict"


def raise_inventory_api_exception(exc: Exception) -> None:
    if isinstance(
        exc,
        StockNotFoundError,
    ):
        raise NotFound(
            detail=str(exc),
            code="stock_not_found",
        ) from exc

    if isinstance(
        exc,
        ReservationNotFoundError,
    ):
        raise NotFound(
            detail=str(exc),
            code="reservation_not_found",
        ) from exc

    if isinstance(
        exc,
        InvalidReservationQuantityError,
    ):
        raise ValidationError(
            detail=str(exc),
            code="invalid_reservation_quantity",
        ) from exc

    if isinstance(
        exc,
        InvalidReservationTTLError,
    ):
        raise ValidationError(
            detail=str(exc),
            code="invalid_reservation_ttl",
        ) from exc

    if isinstance(
        exc,
        IdempotencyConflictError,
    ):
        raise Conflict(
            detail=str(exc),
            code="idempotency_conflict",
        ) from exc

    if isinstance(
        exc,
        InsufficientAvailableStockError,
    ):
        raise Conflict(
            detail=str(exc),
            code="insufficient_available_stock",
        ) from exc

    if isinstance(
        exc,
        InvalidReservationStateError,
    ):
        raise Conflict(
            detail=str(exc),
            code="invalid_reservation_state",
        ) from exc

    if isinstance(
        exc,
        ReservationExpiredError,
    ):
        raise Conflict(
            detail=str(exc),
            code="reservation_expired",
        ) from exc

    if isinstance(
        exc,
        ReservationNotExpiredError,
    ):
        raise Conflict(
            detail=str(exc),
            code="reservation_not_expired",
        ) from exc

    if isinstance(
        exc,
        ProductInactiveError,
    ):
        raise Conflict(
            detail=str(exc),
            code="product_inactive",
        ) from exc

    if isinstance(
        exc,
        WarehouseInactiveError,
    ):
        raise Conflict(
            detail=str(exc),
            code="warehouse_inactive",
        ) from exc

    raise exc