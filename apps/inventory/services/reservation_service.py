import uuid
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.inventory.exceptions import (
    IdempotencyConflictError,
    InsufficientAvailableStockError,
    InvalidReservationQuantityError,
    InvalidReservationTTLError,
    ProductInactiveError,
    StockNotFoundError,
    WarehouseInactiveError,
)
from apps.inventory.models import (
    Reservation,
    Stock,
    StockMovement,
)

class ReservationService:
    DEFAULT_TTL_SECONDS = 15 * 60
    MIN_TTL_SECONDS = 60
    MAX_TTL_SECONDS = 24 * 60 * 60

    @staticmethod
    def _matches_request(*,reservation: Reservation,product_id: uuid.UUID,warehouse_id: uuid.UUID,quantity: int,external_reference: str,) -> bool:
        return (
            reservation.product_id == product_id
            and reservation.warehouse_id == warehouse_id
            and reservation.quantity == quantity
            and reservation.external_reference == external_reference
        )

    @classmethod
    def create_reservation(cls,*,product_id: uuid.UUID,warehouse_id: uuid.UUID,quantity: int,external_reference: str,idempotency_key: str,ttl_seconds: int = DEFAULT_TTL_SECONDS,) -> Reservation:
        if quantity <= 0:
            raise InvalidReservationQuantityError(
                "Reservation quantity must be greater than zero."
            )

        if not (cls.MIN_TTL_SECONDS <= ttl_seconds <= cls.MAX_TTL_SECONDS):
            raise InvalidReservationTTLError("Reservation TTL is outside the allowed range.")

        existing_reservation = Reservation.objects.filter(
            idempotency_key=idempotency_key,
        ).first()

        if existing_reservation is not None:
            if not cls._matches_request(
                reservation=existing_reservation,
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                external_reference=external_reference,
            ):
                raise IdempotencyConflictError(
                    "Idempotency key was already used "
                    "for a different reservation request."
                )

            return existing_reservation

        try:
            with transaction.atomic():
                try:
                    stock = (
                        Stock.objects
                        .select_for_update()
                        .select_related(
                            "product",
                            "warehouse",
                        )
                        .get(
                            product_id=product_id,
                            warehouse_id=warehouse_id,
                        )
                    )
                except Stock.DoesNotExist as exc:
                    raise StockNotFoundError(
                        "Stock for the requested product "
                        "and warehouse does not exist."
                    ) from exc

                # Recheck after obtaining the row lock.
                existing_reservation = Reservation.objects.filter(
                    idempotency_key=idempotency_key,
                ).first()

                if existing_reservation is not None:
                    if not cls._matches_request(
                        reservation=existing_reservation,
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                        quantity=quantity,
                        external_reference=external_reference,
                    ):
                        raise IdempotencyConflictError(
                            "Idempotency key was already used "
                            "for a different reservation request."
                        )

                    return existing_reservation

                if not stock.product.is_active:
                    raise ProductInactiveError(
                        "Inactive products cannot be reserved."
                    )

                if not stock.warehouse.is_active:
                    raise WarehouseInactiveError(
                        "Inactive warehouses cannot accept reservations."
                    )

                if quantity > stock.available_quantity:
                    raise InsufficientAvailableStockError(
                        "Not enough available stock."
                    )

                quantity_before = stock.quantity
                reserved_before = stock.reserved_quantity

                stock.reserved_quantity += quantity

                stock.save(
                    update_fields=(
                        "reserved_quantity",
                        "updated_at",
                    )
                )

                reservation = Reservation.objects.create(
                    product=stock.product,
                    warehouse=stock.warehouse,
                    quantity=quantity,
                    status=Reservation.Status.ACTIVE,
                    external_reference=external_reference,
                    idempotency_key=idempotency_key,
                    expires_at=(
                        timezone.now()
                        + timedelta(seconds=ttl_seconds)
                    ),
                )

                StockMovement.objects.create(
                    stock=stock,
                    reservation=reservation,
                    movement_type=(
                        StockMovement.MovementType.RESERVATION_CREATED
                    ),
                    quantity=quantity,
                    quantity_before=quantity_before,
                    quantity_after=stock.quantity,
                    reserved_before=reserved_before,
                    reserved_after=stock.reserved_quantity,
                    external_reference=external_reference,
                )

                return reservation

        except IntegrityError:
            existing_reservation = Reservation.objects.filter(
                idempotency_key=idempotency_key,
            ).first()

            if existing_reservation is None:
                raise

            if not cls._matches_request(
                reservation=existing_reservation,
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                external_reference=external_reference,
            ):
                raise IdempotencyConflictError(
                    "Idempotency key was already used "
                    "for a different reservation request."
                )

            return existing_reservation