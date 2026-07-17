from datetime import date

import pytest
from django.urls import reverse

from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Task

pytestmark = pytest.mark.django_db


def test_owner_and_manager_create_tasks_but_member_cannot(
    api_authenticate,
    api_users,
    accessible_project,
):
    payload = {
        "project": accessible_project.pk,
        "title": "Create task",
        "assignee": api_users["member"].pk,
    }
    owner_response = api_authenticate(api_users["owner"]).post(
        reverse("task-list"), payload, format="json"
    )
    manager_response = api_authenticate(api_users["manager"]).post(
        reverse("task-list"), {**payload, "title": "Manager task"}, format="json"
    )
    member_response = api_authenticate(api_users["member"]).post(
        reverse("task-list"), {**payload, "title": "Member task"}, format="json"
    )

    assert owner_response.status_code == 201
    assert owner_response.data["creator"] == api_users["owner"].pk
    assert manager_response.status_code == 201
    assert manager_response.data["creator"] == api_users["manager"].pk
    assert member_response.status_code == 403


def test_task_updates_immutable_fields_and_permissions(
    api_authenticate,
    api_users,
    accessible_project,
):
    task = Task.objects.create(
        project=accessible_project,
        title="Existing task",
        creator=api_users["owner"],
    )
    immutable_response = api_authenticate(api_users["owner"]).patch(
        reverse("task-detail", args=[task.pk]),
        {"project": accessible_project.pk, "creator": api_users["manager"].pk},
        format="json",
    )
    manager_response = api_authenticate(api_users["manager"]).patch(
        reverse("task-detail", args=[task.pk]),
        {"status": Task.Status.DONE},
        format="json",
    )
    member_response = api_authenticate(api_users["member"]).patch(
        reverse("task-detail", args=[task.pk]),
        {"status": Task.Status.CANCELLED},
        format="json",
    )
    manager_delete_response = api_authenticate(api_users["manager"]).delete(
        reverse("task-detail", args=[task.pk])
    )
    owner_delete_response = api_authenticate(api_users["owner"]).delete(
        reverse("task-detail", args=[task.pk])
    )

    assert immutable_response.status_code == 400
    assert {"project", "creator"} <= immutable_response.data.keys()
    assert manager_response.status_code == 200
    assert member_response.status_code == 403
    assert manager_delete_response.status_code == 403
    assert owner_delete_response.status_code == 204


def test_task_access_assignees_nullable_fields_and_unrelated_operations(
    api_authenticate,
    api_users,
    accessible_project,
):
    task = Task.objects.create(
        project=accessible_project,
        title="Accessible task",
        creator=api_users["owner"],
    )
    unrelated_project = Project.objects.create(
        name="Hidden", owner=api_users["unrelated"]
    )
    unrelated_task = Task.objects.create(
        project=unrelated_project, title="Hidden task", creator=api_users["unrelated"]
    )
    for user in (api_users["owner"], api_users["manager"], api_users["member"]):
        assert (
            api_authenticate(user)
            .get(reverse("task-detail", args=[task.pk]))
            .status_code
            == 200
        )

    client = api_authenticate(api_users["owner"])
    for method, payload in (
        (client.get, None),
        (client.patch, {"title": "No"}),
        (client.delete, None),
    ):
        response = (
            method(
                reverse("task-detail", args=[unrelated_task.pk]), payload, format="json"
            )
            if payload
            else method(reverse("task-detail", args=[unrelated_task.pk]))
        )
        assert response.status_code == 404

    rejected_assignee = client.post(
        reverse("task-list"),
        {
            "project": accessible_project.pk,
            "title": "Bad assignee",
            "assignee": api_users["unrelated"].pk,
        },
        format="json",
    )
    nullable_task = client.post(
        reverse("task-list"),
        {
            "project": accessible_project.pk,
            "title": "Nullable",
            "assignee": None,
            "due_date": None,
        },
        format="json",
    )
    assert rejected_assignee.status_code == 400
    assert "assignee" in rejected_assignee.data
    assert nullable_task.status_code == 201
    assert nullable_task.data["assignee"] is None
    assert nullable_task.data["due_date"] is None

    for assignee in (api_users["owner"], api_users["manager"], api_users["member"]):
        response = client.post(
            reverse("task-list"),
            {
                "project": accessible_project.pk,
                "title": f"Assigned {assignee.pk}",
                "assignee": assignee.pk,
            },
            format="json",
        )
        assert response.status_code == 201


def test_task_immutable_fields_deletion_and_historical_membership_validation(
    api_authenticate,
    api_users,
    accessible_project,
):
    task = Task.objects.create(
        project=accessible_project,
        title="Immutable",
        creator=api_users["manager"],
        assignee=api_users["member"],
    )
    client = api_authenticate(api_users["owner"])
    create_response = client.post(
        reverse("task-list"),
        {
            "project": accessible_project.pk,
            "title": "No creator",
            "creator": api_users["manager"].pk,
        },
        format="json",
    )
    update_response = client.patch(
        reverse("task-detail", args=[task.pk]),
        {"project": accessible_project.pk, "creator": api_users["manager"].pk},
        format="json",
    )
    assert create_response.status_code == 400
    assert "creator" in create_response.data
    assert update_response.status_code == 400
    assert {"project", "creator"} <= update_response.data.keys()

    ProjectMembership.objects.filter(
        project=accessible_project, user=api_users["manager"]
    ).delete()
    ProjectMembership.objects.filter(
        project=accessible_project, user=api_users["member"]
    ).delete()
    historical_update = client.patch(
        reverse("task-detail", args=[task.pk]),
        {"title": "Still historical"},
        format="json",
    )
    assert historical_update.status_code == 400
    assert {"creator", "assignee"} <= historical_update.data.keys()

    assert (
        api_authenticate(api_users["manager"])
        .get(reverse("task-detail", args=[task.pk]))
        .status_code
        == 404
    )
    assert (
        api_authenticate(api_users["member"])
        .get(reverse("task-detail", args=[task.pk]))
        .status_code
        == 404
    )

    ProjectMembership.objects.create(
        project=accessible_project,
        user=api_users["manager"],
        role=ProjectMembership.Role.MANAGER,
    )
    ProjectMembership.objects.create(
        project=accessible_project,
        user=api_users["member"],
        role=ProjectMembership.Role.MEMBER,
    )
    deletable = Task.objects.create(
        project=accessible_project, title="Delete", creator=api_users["owner"]
    )
    assert (
        api_authenticate(api_users["manager"])
        .get(reverse("task-detail", args=[deletable.pk]))
        .status_code
        == 200
    )
    assert (
        api_authenticate(api_users["member"])
        .get(reverse("task-detail", args=[deletable.pk]))
        .status_code
        == 200
    )
    assert (
        api_authenticate(api_users["manager"])
        .delete(reverse("task-detail", args=[deletable.pk]))
        .status_code
        == 403
    )
    assert (
        api_authenticate(api_users["member"])
        .delete(reverse("task-detail", args=[deletable.pk]))
        .status_code
        == 403
    )
    assert (
        api_authenticate(api_users["owner"])
        .delete(reverse("task-detail", args=[deletable.pk]))
        .status_code
        == 204
    )


def test_task_listing_filters_search_and_isolation(
    api_authenticate,
    api_users,
    accessible_project,
):
    task = Task.objects.create(
        project=accessible_project,
        title="Release platform",
        description="Searchable description",
        creator=api_users["owner"],
        assignee=api_users["member"],
        priority=Task.Priority.HIGH,
        due_date=date(2026, 7, 20),
    )
    unrelated_project = Project.objects.create(
        name="Unrelated",
        owner=api_users["unrelated"],
    )
    unrelated_task = Task.objects.create(
        project=unrelated_project,
        title="Hidden task",
        creator=api_users["unrelated"],
    )
    client = api_authenticate(api_users["member"])
    list_response = client.get(
        reverse("task-list"),
        {
            "project": accessible_project.pk,
            "priority": Task.Priority.HIGH,
            "assignee": api_users["member"].pk,
            "due_date_after": "2026-07-19",
            "search": "Searchable",
            "ordering": "title",
        },
    )
    missing_response = client.get(reverse("task-detail", args=[unrelated_task.pk]))

    assert [item["id"] for item in list_response.data["results"]] == [task.pk]
    assert missing_response.status_code == 404


def test_all_task_filters_search_and_supported_ordering(
    api_authenticate, api_users, accessible_project
):
    other_project = Project.objects.create(
        name="Other accessible", owner=api_users["owner"]
    )
    tasks = [
        Task.objects.create(
            project=accessible_project,
            title="Alpha",
            description="needle description",
            creator=api_users["owner"],
            assignee=api_users["member"],
            status=Task.Status.TODO,
            priority=Task.Priority.LOW,
            due_date=date(2026, 7, 10),
        ),
        Task.objects.create(
            project=accessible_project,
            title="Alpha",
            description="other",
            creator=api_users["owner"],
            assignee=None,
            status=Task.Status.DONE,
            priority=Task.Priority.HIGH,
            due_date=date(2026, 7, 20),
        ),
        Task.objects.create(
            project=other_project,
            title="Zulu",
            description="needle",
            creator=api_users["owner"],
            assignee=api_users["owner"],
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.URGENT,
            due_date=date(2026, 7, 30),
        ),
    ]
    client = api_authenticate(api_users["owner"])
    expected = {
        "project": ("project", str(accessible_project.pk), {tasks[0].pk, tasks[1].pk}),
        "status": ("status", Task.Status.DONE, {tasks[1].pk}),
        "priority": ("priority", Task.Priority.HIGH, {tasks[1].pk}),
        "assignee": ("assignee", str(api_users["member"].pk), {tasks[0].pk}),
        "unassigned": ("unassigned", "true", {tasks[1].pk}),
        "due_date": ("due_date", "2026-07-20", {tasks[1].pk}),
        "due_date_after": ("due_date_after", "2026-07-20", {tasks[1].pk, tasks[2].pk}),
        "due_date_before": (
            "due_date_before",
            "2026-07-20",
            {tasks[0].pk, tasks[1].pk},
        ),
    }
    for field, (parameter, value, ids) in expected.items():
        response = client.get(
            reverse("task-list"), {parameter: value, "page_size": 100}
        )
        assert {item["id"] for item in response.data["results"]} == ids, field

    title_search = client.get(
        reverse("task-list"), {"search": "Alpha", "page_size": 100}
    )
    description_search = client.get(
        reverse("task-list"), {"search": "needle", "page_size": 100}
    )
    assert {item["id"] for item in title_search.data["results"]} == {
        tasks[0].pk,
        tasks[1].pk,
    }
    assert {item["id"] for item in description_search.data["results"]} == {
        tasks[0].pk,
        tasks[2].pk,
    }

    for ordering in ("title", "due_date", "created_at", "updated_at"):
        response = client.get(
            reverse("task-list"), {"ordering": ordering, "page_size": 100}
        )
        ids = [item["id"] for item in response.data["results"]]
        assert (
            ids.index(tasks[0].pk) < ids.index(tasks[1].pk)
            if ordering == "title"
            else len(ids) == 3
        )
    tied = client.get(reverse("task-list"), {"ordering": "title", "page_size": 100})
    tied_ids = [item["id"] for item in tied.data["results"]]
    assert tied_ids.index(tasks[0].pk) < tied_ids.index(tasks[1].pk)
    for unsupported in ("priority", "status"):
        response = client.get(
            reverse("task-list"), {"ordering": unsupported, "page_size": 100}
        )
        default_response = client.get(reverse("task-list"), {"page_size": 100})
        assert [item["id"] for item in response.data["results"]] == [
            item["id"] for item in default_response.data["results"]
        ]
