import factory

from apps.inventory.models import Product, Warehouse, Stock

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