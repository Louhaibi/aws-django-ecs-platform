import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_token_endpoints_are_explicitly_public(api_client, api_users):
    token_response = api_client.post(
        reverse("token-obtain"),
        {"username": api_users["owner"].username, "password": "local-test-password"},
        format="json",
        HTTP_AUTHORIZATION="Bearer malformed",
    )

    assert token_response.status_code == 200
    assert {"access", "refresh"} <= token_response.data.keys()

    refresh_response = api_client.post(
        reverse("token-refresh"),
        {"refresh": token_response.data["refresh"]},
        format="json",
    )
    verify_response = api_client.post(
        reverse("token-verify"),
        {"token": token_response.data["access"]},
        format="json",
    )

    assert refresh_response.status_code == 200
    assert "access" in refresh_response.data
    assert verify_response.status_code == 200


def test_invalid_credentials_are_rejected_without_tokens(api_client, api_users):
    response = api_client.post(
        reverse("token-obtain"),
        {"username": api_users["owner"].username, "password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


def test_invalid_refresh_and_altered_verification_tokens_are_rejected(
    api_client,
    api_users,
):
    token_response = api_client.post(
        reverse("token-obtain"),
        {"username": api_users["owner"].username, "password": "local-test-password"},
        format="json",
    )
    header, payload, signature = token_response.data["access"].split(".")
    replacement = "A" if payload[0] != "A" else "B"
    altered_access = f"{header}.{replacement}{payload[1:]}.{signature}"

    refresh_response = api_client.post(
        reverse("token-refresh"), {"refresh": "not-a-refresh-token"}, format="json"
    )
    verify_response = api_client.post(
        reverse("token-verify"), {"token": altered_access}, format="json"
    )

    assert refresh_response.status_code == 401
    assert verify_response.status_code == 401


def test_protected_endpoints_require_bearer_authentication(api_client):
    for route_name in ("current-user", "project-list", "membership-list", "task-list"):
        response = api_client.get(reverse(route_name))

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Bearer realm="api"'


def test_current_user_only_exposes_safe_fields(api_authenticate, api_users):
    response = api_authenticate(api_users["owner"]).get(reverse("current-user"))

    assert response.status_code == 200
    assert set(response.data) == {"id", "username", "email", "first_name", "last_name"}


def test_jwt_settings_use_a_dedicated_signing_key():
    assert settings.SIMPLE_JWT["SIGNING_KEY"] == settings.JWT_SIGNING_KEY
    assert settings.SIMPLE_JWT["SIGNING_KEY"] != settings.SECRET_KEY
    assert settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() == 15 * 60
    assert settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds() == 24 * 60 * 60


@pytest.mark.parametrize(
    ("setting", "value", "expected_message"),
    (
        ("JWT_SIGNING_KEY", None, "Set the JWT_SIGNING_KEY environment variable"),
        ("JWT_SIGNING_KEY", "", "JWT_SIGNING_KEY must be set and non-empty."),
        ("JWT_SIGNING_KEY", "   ", "JWT_SIGNING_KEY must be set and non-empty."),
        ("JWT_ACCESS_TOKEN_MINUTES", "0", "JWT_ACCESS_TOKEN_MINUTES must be positive."),
        (
            "JWT_ACCESS_TOKEN_MINUTES",
            "-1",
            "JWT_ACCESS_TOKEN_MINUTES must be positive.",
        ),
        ("JWT_REFRESH_TOKEN_DAYS", "0", "JWT_REFRESH_TOKEN_DAYS must be positive."),
        ("JWT_REFRESH_TOKEN_DAYS", "-1", "JWT_REFRESH_TOKEN_DAYS must be positive."),
    ),
)
def test_settings_reject_unsafe_jwt_configuration(setting, value, expected_message):
    environment = {
        "DJANGO_SECRET_KEY": "test-django-secret-key",
        "DATABASE_URL": "postgresql://test:test@127.0.0.1:5432/test",
        "DJANGO_DEBUG": "False",
        "DJANGO_ALLOWED_HOSTS": "",
    }
    configured_signing_key = "test-signing-key-value-that-must-not-appear"
    environment["JWT_SIGNING_KEY"] = configured_signing_key
    if value is None:
        environment.pop(setting, None)
    else:
        environment[setting] = value

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import environ; "
                "environ.Env.read_env = lambda *args, **kwargs: None; "
                "import config.settings"
            ),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0
    output = f"{result.stdout}\n{result.stderr}"
    assert expected_message in output
    assert configured_signing_key not in output
