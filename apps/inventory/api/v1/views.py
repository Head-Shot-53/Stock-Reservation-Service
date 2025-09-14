from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.exceptions import InventoryError
from apps.inventory.models import Reservation, Stock
from apps.inventory.services import ReservationService

from .exceptions import raise_inventory_api_exception
from .serializers import (
    AvailabilityQuerySerializer,
    AvailabilitySerializer,
    CreateReservationSerializer,
    ReservationSerializer,
)

class AvailabilityView(APIView):
    def get(self, request):
        query_serializer = AvailabilityQuerySerializer(
            data=request.query_params,
        )
        query_serializer.is_valid(
            raise_exception=True,
        )

        product_id = query_serializer.validated_data[
            "product_id"
        ]
        warehouse_id = query_serializer.validated_data[
            "warehouse_id"
        ]

        try:
            stock = (
                Stock.objects
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
            raise NotFound(
                "Stock for the requested product and warehouse does not exist."
            ) from exc

        serializer = AvailabilitySerializer(
            {
                "product_id": stock.product_id,
                "warehouse_id": stock.warehouse_id,
                "quantity": stock.quantity,
                "reserved_quantity": stock.reserved_quantity,
                "available_quantity": stock.available_quantity,
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ReservationCreateView(APIView):
    def post(self, request):
        serializer = CreateReservationSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        idempotency_key = request.headers.get(
            "Idempotency-Key"
        )

        if not idempotency_key:
            raise ValidationError(
                {
                    "Idempotency-Key": (
                        "This header is required."
                    )
                }
            )

        try:
            reservation = (
                ReservationService.create_reservation(
                    product_id=serializer.validated_data[
                        "product_id"
                    ],
                    warehouse_id=serializer.validated_data[
                        "warehouse_id"
                    ],
                    quantity=serializer.validated_data[
                        "quantity"
                    ],
                    external_reference=serializer.validated_data[
                        "external_reference"
                    ],
                    idempotency_key=idempotency_key,
                    ttl_seconds=serializer.validated_data[
                        "ttl_seconds"
                    ],
                )
            )

        except InventoryError as exc:
            raise_inventory_api_exception(exc)

        output_serializer = ReservationSerializer(
            reservation,
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ReservationDetailView(APIView):
    def get(self, request, reservation_id):
        try:
            reservation = (
                Reservation.objects
                .select_related(
                    "product",
                    "warehouse",
                )
                .get(id=reservation_id)
            )
        except Reservation.DoesNotExist as exc:
            raise NotFound(
                "Reservation does not exist."
            ) from exc

        serializer = ReservationSerializer(
            reservation,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ReservationConfirmView(APIView):
    def post(self,request,reservation_id):
        try:
            reservation = (
                ReservationService.confirm_reservation(
                    reservation_id=reservation_id,
                )
            )

        except InventoryError as exc:
            raise_inventory_api_exception(exc)

        serializer = ReservationSerializer(
            reservation,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ReservationCancelView(APIView):
    def post(self,request,reservation_id):
        try:
            reservation = (
                ReservationService.cancel_reservation(
                    reservation_id=reservation_id,
                )
            )

        except InventoryError as exc:
            raise_inventory_api_exception(exc)

        serializer = ReservationSerializer(
            reservation,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )