import pytest
from django.urls import reverse

from apps.projects.models import Project

pytestmark = pytest.mark.django_db


def test_project_creation_assigns_request_user_and_rejects_owner_input(
    api_authenticate,
    api_users,
):
    response = api_authenticate(api_users["owner"]).post(
        reverse("project-list"),
        {"name": "Created project", "description": "API project"},
        format="json",
    )
    rejected_response = api_authenticate(api_users["owner"]).post(
        reverse("project-list"),
        {"name": "Rejected project", "owner": api_users["unrelated"].pk},
        format="json",
    )

    project = Project.objects.get(pk=response.data["id"])
    assert response.status_code == 201
    assert project.owner == api_users["owner"]
    assert rejected_response.status_code == 400
    assert "owner" in rejected_response.data


def test_projects_are_isolated_and_owner_controls_mutation(
    api_authenticate,
    api_users,
    accessible_project,
):
    unrelated_project = Project.objects.create(
        name="Unrelated project",
        owner=api_users["unrelated"],
    )
    list_response = api_authenticate(api_users["member"]).get(reverse("project-list"))
    forbidden_response = api_authenticate(api_users["manager"]).patch(
        reverse("project-detail", args=[accessible_project.pk]),
        {"name": "Manager cannot change this"},
        format="json",
    )
    missing_response = api_authenticate(api_users["owner"]).get(
        reverse("project-detail", args=[unrelated_project.pk])
    )
    owner_response = api_authenticate(api_users["owner"]).patch(
        reverse("project-detail", args=[accessible_project.pk]),
        {"name": "Owner update"},
        format="json",
    )

    assert [project["id"] for project in list_response.data["results"]] == [
        accessible_project.pk
    ]
    assert forbidden_response.status_code == 403
    assert missing_response.status_code == 404
    assert owner_response.status_code == 200
    assert owner_response.data["name"] == "Owner update"


def test_project_delete_and_unrelated_detail_operations(
    api_authenticate,
    api_users,
    accessible_project,
):
    unrelated_project = Project.objects.create(
        name="Unrelated project", owner=api_users["unrelated"]
    )
    client = api_authenticate(api_users["unrelated"])

    for method, payload in (
        (client.get, None),
        (client.patch, {"name": "Nope"}),
        (client.delete, None),
    ):
        kwargs = {"format": "json"} if payload is not None else {}
        response = (
            method(
                reverse("project-detail", args=[accessible_project.pk]),
                payload,
                **kwargs,
            )
            if payload is not None
            else method(reverse("project-detail", args=[accessible_project.pk]))
        )
        assert response.status_code == 404

    assert (
        api_authenticate(api_users["manager"])
        .delete(reverse("project-detail", args=[unrelated_project.pk]))
        .status_code
        == 404
    )
    assert (
        api_authenticate(api_users["manager"])
        .delete(reverse("project-detail", args=[accessible_project.pk]))
        .status_code
        == 403
    )
    assert (
        api_authenticate(api_users["member"])
        .delete(reverse("project-detail", args=[accessible_project.pk]))
        .status_code
        == 403
    )
    assert (
        api_authenticate(api_users["owner"])
        .delete(reverse("project-detail", args=[accessible_project.pk]))
        .status_code
        == 204
    )


def test_project_pagination_page_size_and_immutable_owner_on_patch(
    api_authenticate,
    api_users,
):
    projects = [
        Project.objects.create(name=f"Project {number}", owner=api_users["owner"])
        for number in range(101)
    ]
    client = api_authenticate(api_users["owner"])
    first_page = client.get(reverse("project-list"), {"ordering": "name"})
    sized_page = client.get(
        reverse("project-list"), {"page_size": 2, "ordering": "name"}
    )
    capped_page = client.get(reverse("project-list"), {"page_size": 1000})
    owner_patch = client.patch(
        reverse("project-detail", args=[projects[0].pk]),
        {"owner": api_users["unrelated"].pk},
        format="json",
    )

    assert first_page.data["count"] == 101
    assert len(first_page.data["results"]) == 20
    assert len(sized_page.data["results"]) == 2
    assert len(capped_page.data["results"]) == 100
    assert owner_patch.status_code == 400
    assert "owner" in owner_patch.data


def test_project_search_ordering_and_put_behavior(api_authenticate, api_users):
    client = api_authenticate(api_users["owner"])
    first = Project.objects.create(name="Alpha platform", owner=api_users["owner"])
    second = Project.objects.create(name="Beta platform", owner=api_users["owner"])

    search_response = client.get(reverse("project-list"), {"search": "Alpha"})
    ordering_response = client.get(reverse("project-list"), {"ordering": "name"})
    put_response = client.put(
        reverse("project-detail", args=[first.pk]),
        {"name": "Not supported"},
        format="json",
    )

    assert [project["id"] for project in search_response.data["results"]] == [first.pk]
    assert [project["id"] for project in ordering_response.data["results"]] == [
        first.pk,
        second.pk,
    ]
    assert put_response.status_code == 405
