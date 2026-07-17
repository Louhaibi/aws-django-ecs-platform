import pytest
from rest_framework.test import APIClient

from apps.projects.models import Project, ProjectMembership


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_authenticate(api_client):
    def authenticate(user):
        api_client.force_authenticate(user=user)
        return api_client

    return authenticate


@pytest.fixture
def api_users(user_factory):
    return {
        "owner": user_factory("api-owner", password="local-test-password"),
        "manager": user_factory("api-manager", password="local-test-password"),
        "member": user_factory("api-member", password="local-test-password"),
        "unrelated": user_factory(
            "api-unrelated",
            password="local-test-password",
        ),
    }


@pytest.fixture
def accessible_project(api_users):
    project = Project.objects.create(
        name="Accessible project", owner=api_users["owner"]
    )
    ProjectMembership.objects.create(
        project=project,
        user=api_users["manager"],
        role=ProjectMembership.Role.MANAGER,
    )
    ProjectMembership.objects.create(project=project, user=api_users["member"])
    return project
