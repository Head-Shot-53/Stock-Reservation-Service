from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.exceptions import InventoryError
from apps.inventory.models import Reservation, Stock
from apps.inventory.services import ReservationService
from apps.inventory.selectors import (
    get_reservation,
    get_stock,
    list_reservations,
)

from .exceptions import raise_inventory_api_exception
from .pagination import ReservationPagination
from .serializers import (
    AvailabilityQuerySerializer,
    AvailabilitySerializer,
    CreateReservationSerializer,
    ErrorResponseSerializer,
    PaginatedReservationListSerializer,
    ReservationListQuerySerializer,
    ReservationSerializer,
)

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)


class AvailabilityView(APIView):

    @extend_schema(
        operation_id="stock_availability",
        tags=["Inventory"],
        summary="Get stock availability",
        description=(
            "Returns the physical, reserved and available "
            "quantity for a product in a warehouse."
        ),
        parameters=[
            AvailabilityQuerySerializer,
        ],
        responses={
            200: AvailabilitySerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def get(self, request):
        query_serializer = AvailabilityQuerySerializer(
            data=request.query_params,
        )

        query_serializer.is_valid(
            raise_exception=True,
        )

        try:
            stock = get_stock(
                product_id=query_serializer.validated_data[
                    "product_id"
                ],
                warehouse_id=query_serializer.validated_data[
                    "warehouse_id"
                ],
            )
        except InventoryError as exc:
            raise_inventory_api_exception(exc)

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


class ReservationListCreateView(APIView):

    @extend_schema(
        operation_id="reservation_create",
        tags=["Reservations"],
        summary="Create a reservation",
        description=(
            "Creates a temporary stock reservation. "
            "The operation is idempotent when the same "
            "Idempotency-Key and payload are used."
        ),
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description=(
                    "Unique key used to safely retry "
                    "reservation creation."
                ),
            ),
        ],
        request=CreateReservationSerializer,
        responses={
            201: ReservationSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request validation failed.",
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "Stock for the requested product "
                    "and warehouse does not exist."
                ),
            ),
            409: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "The request conflicts with "
                    "the current inventory state."
                ),
                examples=[
                    OpenApiExample(
                        "Insufficient stock",
                        value={
                            "error": {
                                "code": (
                                    "insufficient_available_stock"
                                ),
                                "message": (
                                    "Not enough available stock."
                                ),
                                "details": {},
                            }
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
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

    @extend_schema(
        operation_id="reservation_list",
        tags=["Reservations"],
        summary="List reservations",
        description=(
            "Returns a paginated list of reservations. "
            "Results can be filtered by status, product, "
            "warehouse and external reference."
        ),
        parameters=[
            ReservationListQuerySerializer,
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Page number.",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Number of results per page. Maximum 100."
                ),
            ),
        ],
        responses={
            200: PaginatedReservationListSerializer,
            400: ErrorResponseSerializer,
        },
    )
    def get(self, request):
        query_serializer = ReservationListQuerySerializer(
            data=request.query_params,
        )

        query_serializer.is_valid(
            raise_exception=True,
        )

        reservations = list_reservations(
            **query_serializer.validated_data,
        )

        paginator = ReservationPagination()

        page = paginator.paginate_queryset(
            reservations,
            request,
            view=self,
        )

        serializer = ReservationSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data,
        )


class ReservationDetailView(APIView):

    @extend_schema(
        operation_id="reservation_retrieve",
        tags=["Reservations"],
        summary="Get reservation details",
        description=(
            "Returns the current state of a reservation."
        ),
        responses={
            200: ReservationSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def get(self, request, reservation_id):
        try:
            reservation = get_reservation(
                reservation_id=reservation_id,
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


class ReservationConfirmView(APIView):

    @extend_schema(
        operation_id="reservation_confirm",
        tags=["Reservations"],
        summary="Confirm a reservation",
        description=(
            "Confirms an ACTIVE reservation and permanently "
            "deducts the reserved quantity from physical stock. "
            "Repeated confirmation is idempotent."
        ),
        request=None,
        responses={
            200: ReservationSerializer,
            404: ErrorResponseSerializer,
            409: ErrorResponseSerializer,
        },
    )
    def post(self, request, reservation_id):
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

    @extend_schema(
        operation_id="reservation_cancel",
        tags=["Reservations"],
        summary="Cancel a reservation",
        description=(
            "Cancels an ACTIVE reservation and releases "
            "its reserved stock. Repeated cancellation "
            "is idempotent."
        ),
        request=None,
        responses={
            200: ReservationSerializer,
            404: ErrorResponseSerializer,
            409: ErrorResponseSerializer,
        },
    )
    def post(self, request, reservation_id):
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