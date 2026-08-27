import uuid

import pytest
from django.db import IntegrityError, transaction

from apps.inventory.models import Stock
from apps.inventory.tests.factories import (
    ProductFactory,
    StockFactory,
    WarehouseFactory,
)

pytestmark = pytest.mark.django_db


def test_stock_is_created_with_expected_values():
    product = ProductFactory(
        sku="PS5-GOW-RAGNAROK",
        name="God of War Ragnarök PS5",
    )
    warehouse = WarehouseFactory(
        code="WRO-GAMES-01",
    )

    stock = StockFactory(
        product=product,
        warehouse=warehouse,
        quantity=10,
        reserved_quantity=3,
    )

    assert isinstance(stock.id, uuid.UUID)
    assert stock.product == product
    assert stock.warehouse == warehouse
    assert stock.quantity == 10
    assert stock.reserved_quantity == 3
    assert stock.created_at is not None
    assert stock.updated_at is not None


def test_stock_quantities_are_zero_by_default():
    stock = StockFactory()

    assert stock.quantity == 0
    assert stock.reserved_quantity == 0
    assert stock.available_quantity == 0


def test_stock_calculates_available_quantity():
    stock = StockFactory(
        quantity=10,
        reserved_quantity=3,
    )

    assert stock.available_quantity == 7


def test_stock_string_representation():
    product = ProductFactory(
        sku="PS5-GOW-RAGNAROK",
        name="God of War Ragnarök PS5",
    )
    warehouse = WarehouseFactory(
        code="WRO-GAMES-01",
    )

    stock = StockFactory(
        product=product,
        warehouse=warehouse,
    )

    assert str(stock) == "PS5-GOW-RAGNAROK @ WRO-GAMES-01"


def test_product_and_warehouse_pair_is_unique():
    product = ProductFactory(
        sku="PS5-SPIDER-MAN-2",
        name="Marvel's Spider-Man 2 PS5",
    )
    warehouse = WarehouseFactory(
        code="WRO-GAMES-01",
    )

    StockFactory(
        product=product,
        warehouse=warehouse,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockFactory(
                product=product,
                warehouse=warehouse,
            )


def test_same_product_can_exist_in_different_warehouses():
    product = ProductFactory(
        sku="PS5-FINAL-FANTASY-16",
        name="Final Fantasy XVI PS5",
    )

    first_warehouse = WarehouseFactory(
        code="WRO-GAMES-01",
    )
    second_warehouse = WarehouseFactory(
        code="LEG-GAMES-01",
    )

    first_stock = StockFactory(
        product=product,
        warehouse=first_warehouse,
    )
    second_stock = StockFactory(
        product=product,
        warehouse=second_warehouse,
    )

    assert Stock.objects.filter(
        product=product,
    ).count() == 2

    assert first_stock.warehouse != second_stock.warehouse


def test_different_products_can_exist_in_same_warehouse():
    warehouse = WarehouseFactory(
        code="WRO-GAMES-01",
    )

    first_product = ProductFactory(
        sku="PS5-HORIZON-FW",
        name="Horizon Forbidden West PS5",
    )
    second_product = ProductFactory(
        sku="PS5-GRAN-TURISMO-7",
        name="Gran Turismo 7 PS5",
    )

    first_stock = StockFactory(
        product=first_product,
        warehouse=warehouse,
    )
    second_stock = StockFactory(
        product=second_product,
        warehouse=warehouse,
    )

    assert Stock.objects.filter(
        warehouse=warehouse,
    ).count() == 2

    assert first_stock.product != second_stock.product


def test_quantity_cannot_be_negative():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockFactory(
                quantity=-1,
                reserved_quantity=0,
            )


def test_reserved_quantity_cannot_be_negative():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockFactory(
                quantity=10,
                reserved_quantity=-1,
            )


def test_reserved_quantity_cannot_exceed_quantity():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockFactory(
                quantity=5,
                reserved_quantity=6,
            )