import pytest


@pytest.fixture
def user_factory(django_user_model):
    def create_user(username, **kwargs):
        return django_user_model.objects.create_user(username=username, **kwargs)

    return create_user
