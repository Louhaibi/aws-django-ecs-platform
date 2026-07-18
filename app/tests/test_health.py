import pytest
from django.db import OperationalError
from django.urls import reverse


@pytest.mark.django_db
def test_health_returns_only_approved_fields_when_database_is_available(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_health_returns_controlled_response_when_database_is_unavailable(
    client,
    monkeypatch,
):
    def unavailable_cursor():
        raise OperationalError("database unavailable")

    monkeypatch.setattr("config.views.connection.cursor", unavailable_cursor)

    response = client.get(reverse("health"))

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy"}
    assert b"database unavailable" not in response.content


def test_health_rejects_non_get_requests(client):
    response = client.post(reverse("health"))

    assert response.status_code == 405
