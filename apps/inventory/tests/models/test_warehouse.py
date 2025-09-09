import uuid

import pytest
from django.db import IntegrityError, transaction

from apps.inventory.models import Warehouse
from apps.inventory.tests.factories import WarehouseFactory


pytestmark = pytest.mark.django_db


import uuid

import pytest
from django.db import IntegrityError, transaction

from apps.inventory.models import Warehouse
from apps.inventory.tests.factories import WarehouseFactory


pytestmark = pytest.mark.django_db


def test_warehouse_is_created_with_expected_values():
    warehouse = WarehouseFactory(
        code="DRO-01",
        name="Dnipro Main Warehouse",
        address="Dnipro, Ukraine",
    )

    assert isinstance(warehouse.id, uuid.UUID)
    assert warehouse.code == "DRO-01"
    assert warehouse.name == "Dnipro Main Warehouse"
    assert warehouse.address == "Dnipro, Ukraine"
    assert warehouse.is_active is True
    assert warehouse.created_at is not None
    assert warehouse.updated_at is not None


def test_warehouse_string_representation():
    warehouse = WarehouseFactory(
        code="DRO-01",
        name="Dnipro Main Warehouse",
    )

    assert str(warehouse) == (
        "DRO-01 — Dnipro Main Warehouse"
    )


def test_warehouse_address_is_empty_by_default():
    warehouse = WarehouseFactory()

    assert warehouse.address == ""


def test_warehouse_code_is_unique_case_insensitively():
    WarehouseFactory(
        code="DRO-01",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            WarehouseFactory(
                code="dro-01",
            )


def test_warehouses_are_ordered_by_code():
    WarehouseFactory(
        code="DRO-03",
    )
    WarehouseFactory(
        code="DRO-01",
    )
    WarehouseFactory(
        code="DRO-02",
    )

    codes = list(
        Warehouse.objects.values_list(
            "code",
            flat=True,
        )
    )

    assert codes == [
        "DRO-01",
        "DRO-02",
        "DRO-03",
    ]