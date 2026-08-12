import factory

from apps.inventory.models import Product, Warehouse, Stock, Reservation

from datetime import timedelta
from django.utils import timezone

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    sku = factory.Sequence(lambda number: f"PRODUCT-{number:05d}")

    name = factory.Sequence(lambda number: f"Product {number}")

    description = ""
    is_active = True


class WarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Warehouse

    code = factory.Sequence(lambda number: F"WAREHOUSE-{number:05d}")

    name = factory.Sequence(lambda number: f"Warehouse {number}")

    address = ""
    is_active = True


class StockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stock

    product = factory.SubFactory(ProductFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    quantity = 0
    reserved_quantity = 0


class ReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reservation

    product = factory.SubFactory(ProductFactory)
    warehouse = factory.SubFactory(WarehouseFactory)

    quantity = 1

    status = Reservation.Status.ACTIVE

    external_reference = factory.Sequence(
        lambda number: f"ORDER-{number:05d}"
    )

    idempotency_key = factory.Sequence(
        lambda number: f"IDEMPOTENCY-{number:05d}"
    )

    expires_at = factory.LazyFunction(
        lambda: timezone.now() + timedelta(minutes=15)
    )