import pytest
from django.urls import reverse

from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Task

pytestmark = pytest.mark.django_db


def test_project_list_owner_summaries_do_not_add_queries_per_row(
    api_authenticate, api_users, django_assert_num_queries
):
    for number in range(4):
        Project.objects.create(name=f"Project {number}", owner=api_users["owner"])

    with django_assert_num_queries(2):
        response = api_authenticate(api_users["owner"]).get(
            reverse("project-list"), {"page_size": 100}
        )

    assert len(response.data["results"]) == 4


def test_membership_list_summaries_do_not_add_queries_per_row(
    api_authenticate, api_users, django_assert_num_queries
):
    projects = [
        Project.objects.create(name=f"Project {number}", owner=api_users["owner"])
        for number in range(4)
    ]
    for project in projects:
        ProjectMembership.objects.create(project=project, user=api_users["member"])

    with django_assert_num_queries(2):
        response = api_authenticate(api_users["owner"]).get(
            reverse("membership-list"), {"page_size": 100}
        )

    assert len(response.data["results"]) == 4


def test_task_list_summaries_do_not_add_queries_per_row(
    api_authenticate, api_users, django_assert_num_queries
):
    project = Project.objects.create(name="Project", owner=api_users["owner"])
    ProjectMembership.objects.create(project=project, user=api_users["manager"])
    ProjectMembership.objects.create(project=project, user=api_users["member"])
    for number in range(4):
        Task.objects.create(
            project=project,
            title=f"Task {number}",
            creator=api_users["manager"],
            assignee=api_users["member"],
        )

    with django_assert_num_queries(2):
        response = api_authenticate(api_users["owner"]).get(
            reverse("task-list"), {"page_size": 100}
        )

    assert len(response.data["results"]) == 4
