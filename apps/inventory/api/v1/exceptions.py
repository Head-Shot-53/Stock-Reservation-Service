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
    default_detail = "The request conflicts with the current resource state."
    default_code = "conflict"


def raise_inventory_api_exception(exc: Exception) -> None:
    if isinstance(exc,
        (
            StockNotFoundError,
            ReservationNotFoundError,
        ),
    ):
        raise NotFound(
            detail=str(exc),
        ) from exc

    if isinstance(exc,
        (
            InvalidReservationQuantityError,
            InvalidReservationTTLError,
        ),
    ):
        raise ValidationError(
            detail=str(exc),
        ) from exc

    if isinstance(exc,
        (
            IdempotencyConflictError,
            InsufficientAvailableStockError,
            InvalidReservationStateError,
            ProductInactiveError,
            ReservationExpiredError,
            ReservationNotExpiredError,
            WarehouseInactiveError,
        ),
    ):
        raise Conflict(
            detail=str(exc),
        ) from exc

    raise exc