import uuid

import pytest
from django.db import IntegrityError, transaction

from apps.inventory.models import Product
from apps.inventory.tests.factories import ProductFactory


pytestmark = pytest.mark.django_db

def test_product_is_created_with_expected_values():
    product = ProductFactory(
        sku = "PS5-GOW-RAGNAROK",
        name = "God of War Ragnarök PS5",
        description="Game disc for PlayStation 5",
    )

    assert isinstance(product.id, uuid.UUID)
    assert product.sku == "PS5-GOW-RAGNAROK"
    assert product.name == "God of War Ragnarök PS5"
    assert product.description == "Game disc for PlayStation 5"
    assert product.is_active is True
    assert product.created_at is not None
    assert product.updated_at is not None


def test_product_string_representation():
    product = ProductFactory(
            sku = "PS5-GOW-RAGNAROK",
            name = "God of War Ragnarök PS5",
        )

    assert str(product) == ("PS5-GOW-RAGNAROK — God of War Ragnarök PS5")


def test_product_description_is_empty_by_default():
    product = ProductFactory()

    assert product.description == ""


def test_product_sku_is_unique_case_insensitively():
    ProductFactory(
        sku = "PS5-GOW-RAGNAROK"
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProductFactory(
                sku = "ps5-gow-ragnarok"
            )


def test_products_are_ordered_by_sku():
    ProductFactory(
        sku="PS5-SPIDER-MAN-2",
        name="Marvel's Spider-Man 2 PS5",
    )
    ProductFactory(
        sku="PS5-FINAL-FANTASY-16",
        name="Final Fantasy XVI PS5",
    )
    ProductFactory(
        sku="PS5-HORIZON-FW",
        name="Horizon Forbidden West PS5",
    )

    skus = list(
        Product.objects.values_list("sku", flat=True)
    )

    assert skus == [
        "PS5-FINAL-FANTASY-16",
        "PS5-HORIZON-FW",
        "PS5-SPIDER-MAN-2",
    ]