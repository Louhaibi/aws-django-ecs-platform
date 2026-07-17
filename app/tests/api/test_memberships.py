from types import SimpleNamespace

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import serializers

from apps.api.views import ProjectMembershipViewSet
from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Task

pytestmark = pytest.mark.django_db


def test_owner_manages_memberships_and_others_are_read_only(
    api_authenticate,
    api_users,
    accessible_project,
):
    client = api_authenticate(api_users["owner"])
    create_response = client.post(
        reverse("membership-list"),
        {
            "project": accessible_project.pk,
            "user": api_users["unrelated"].pk,
            "role": ProjectMembership.Role.MANAGER,
        },
        format="json",
    )
    membership_id = create_response.data["id"]
    update_response = client.patch(
        reverse("membership-detail", args=[membership_id]),
        {"role": ProjectMembership.Role.MEMBER},
        format="json",
    )
    forbidden_response = api_authenticate(api_users["manager"]).delete(
        reverse("membership-detail", args=[membership_id])
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert forbidden_response.status_code == 403


def test_membership_isolation_validation_and_immutable_relationships(
    api_authenticate,
    api_users,
    accessible_project,
):
    membership = ProjectMembership.objects.get(
        project=accessible_project,
        user=api_users["member"],
    )
    duplicate_response = api_authenticate(api_users["owner"]).post(
        reverse("membership-list"),
        {"project": accessible_project.pk, "user": api_users["member"].pk},
        format="json",
    )
    immutable_response = api_authenticate(api_users["owner"]).patch(
        reverse("membership-detail", args=[membership.pk]),
        {"project": accessible_project.pk, "user": api_users["member"].pk},
        format="json",
    )
    owner_membership_response = api_authenticate(api_users["owner"]).post(
        reverse("membership-list"),
        {"project": accessible_project.pk, "user": api_users["owner"].pk},
        format="json",
    )

    assert duplicate_response.status_code == 400
    assert "non_field_errors" in duplicate_response.data
    assert immutable_response.status_code == 400
    assert "user" in immutable_response.data
    assert "project" in immutable_response.data
    assert owner_membership_response.status_code == 400
    assert "user" in owner_membership_response.data


def test_duplicate_membership_integrity_error_uses_savepoint(
    api_users,
    accessible_project,
):
    existing_membership = ProjectMembership.objects.get(
        project=accessible_project,
        user=api_users["member"],
    )

    class DuplicateSerializer:
        validated_data = {
            "project": accessible_project,
            "user": api_users["member"],
        }

        def save(self):
            return ProjectMembership.objects.bulk_create(
                [
                    ProjectMembership(
                        project=accessible_project,
                        user=api_users["member"],
                    )
                ]
            )

    view = ProjectMembershipViewSet()
    view.request = SimpleNamespace(user=api_users["owner"])

    with transaction.atomic():
        with pytest.raises(serializers.ValidationError) as exc_info:
            view.perform_create(DuplicateSerializer())

        assert "non_field_errors" in exc_info.value.detail
        assert (
            ProjectMembership.objects.get(pk=existing_membership.pk)
            == existing_membership
        )


def test_unrelated_membership_integrity_error_is_reraised(
    api_users, accessible_project
):
    class BrokenSerializer:
        validated_data = {
            "project": accessible_project,
            "user": api_users["unrelated"],
        }

        def save(self):
            raise IntegrityError("synthetic unrelated integrity error")

    view = ProjectMembershipViewSet()
    view.request = SimpleNamespace(user=api_users["owner"])

    with pytest.raises(IntegrityError):
        view.perform_create(BrokenSerializer())


def test_membership_lists_filters_permissions_and_history(
    api_authenticate,
    api_users,
    accessible_project,
    user_factory,
):
    unrelated_project = Project.objects.create(
        name="Unrelated", owner=api_users["unrelated"]
    )
    unrelated_user = user_factory("unrelated-membership-user")
    unrelated_membership = ProjectMembership.objects.create(
        project=unrelated_project, user=unrelated_user
    )
    manager_membership = ProjectMembership.objects.get(
        project=accessible_project, user=api_users["manager"]
    )
    task = Task.objects.create(
        project=accessible_project,
        title="Historical people",
        creator=api_users["manager"],
        assignee=api_users["member"],
    )

    for user in (api_users["owner"], api_users["manager"], api_users["member"]):
        response = api_authenticate(user).get(reverse("membership-list"))
        assert {entry["project"] for entry in response.data["results"]} == {
            accessible_project.pk
        }

    client = api_authenticate(api_users["member"])
    assert (
        client.get(
            reverse("membership-detail", args=[unrelated_membership.pk])
        ).status_code
        == 404
    )
    assert (
        client.get(reverse("membership-list"), {"project": unrelated_project.pk}).data[
            "results"
        ]
        == []
    )
    assert (
        client.get(
            reverse("membership-list"), {"role": ProjectMembership.Role.MANAGER}
        ).data["results"][0]["id"]
        == manager_membership.pk
    )

    for user in (api_users["manager"], api_users["member"]):
        client = api_authenticate(user)
        assert (
            client.post(
                reverse("membership-list"),
                {"project": accessible_project.pk, "user": api_users["unrelated"].pk},
                format="json",
            ).status_code
            == 403
        )
        assert (
            client.patch(
                reverse("membership-detail", args=[manager_membership.pk]),
                {"role": ProjectMembership.Role.MEMBER},
                format="json",
            ).status_code
            == 403
        )
        assert (
            client.delete(
                reverse("membership-detail", args=[manager_membership.pk])
            ).status_code
            == 403
        )

    assert (
        api_authenticate(api_users["owner"])
        .delete(reverse("membership-detail", args=[manager_membership.pk]))
        .status_code
        == 204
    )
    task.refresh_from_db()
    assert task.creator_id == api_users["manager"].pk
    assert task.assignee_id == api_users["member"].pk
