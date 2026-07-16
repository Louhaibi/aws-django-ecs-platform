import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


def test_admin_login_page_responds(client):
    response = client.get(reverse("admin:login"))

    assert response.status_code == 200


def test_custom_user_model_is_configured_and_registered():
    user_model = get_user_model()

    assert issubclass(user_model, AbstractUser)
    assert user_model._meta.label == "users.User"
    assert admin.site.is_registered(user_model)


@pytest.mark.django_db
def test_custom_user_can_be_persisted():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="validation-user",
        password="unsafe-local-test-password",
    )

    assert user.pk is not None
    assert user.check_password("unsafe-local-test-password")
