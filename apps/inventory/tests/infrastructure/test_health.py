import pytest

def test_health_endpoint_returns_ok(client):
    response = client.get(
        "/health/",
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "service": "stock-reservation-service",
    }


@pytest.mark.django_db
def test_readiness_returns_ready_when_dependencies_are_available(client,monkeypatch):
    monkeypatch.setattr(
        "config.health._redis_is_ready",
        lambda: True,
    )

    response = client.get(
        "/ready/",
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ready",
        "checks": {
            "database": True,
            "redis": True,
        },
    }

@pytest.mark.django_db
def test_readiness_returns_503_when_redis_is_unavailable(client,monkeypatch):
    monkeypatch.setattr(
        "config.health._redis_is_ready",
        lambda: False,
    )

    response = client.get(
        "/ready/",
    )

    assert response.status_code == 503

    data = response.json()

    assert data["status"] == "not_ready"
    assert data["checks"]["database"] is True
    assert data["checks"]["redis"] is False

def test_readiness_returns_503_when_database_is_unavailable(client,monkeypatch):
    monkeypatch.setattr(
        "config.health._database_is_ready",
        lambda: False,
    )

    monkeypatch.setattr(
        "config.health._redis_is_ready",
        lambda: True,
    )

    response = client.get(
        "/ready/",
    )

    assert response.status_code == 503

    data = response.json()

    assert data["status"] == "not_ready"
    assert data["checks"]["database"] is False
    assert data["checks"]["redis"] is True