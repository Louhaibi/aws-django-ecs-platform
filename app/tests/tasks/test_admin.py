import pytest
from django.contrib import admin
from django.core.exceptions import NON_FIELD_ERRORS
from django.test import RequestFactory

from apps.projects.models import Project, ProjectMembership
from apps.tasks.admin import TaskAdmin
from apps.tasks.models import Task

pytestmark = pytest.mark.django_db


def test_task_is_registered_with_admin():
    assert admin.site.is_registered(Task)
    assert isinstance(admin.site._registry[Task], TaskAdmin)


def test_task_admin_configuration():
    task_admin = admin.site._registry[Task]

    assert "status" in task_admin.list_display
    assert "priority" in task_admin.list_display
    assert "status" in task_admin.list_filter
    assert "priority" in task_admin.list_filter
    assert task_admin.autocomplete_fields == ("project", "assignee", "creator")


def test_task_creator_is_readonly_only_on_change(user_factory):
    request = RequestFactory().get("/admin/")
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)
    task = Task.objects.create(project=project, title="Plan rollout", creator=owner)
    task_admin = admin.site._registry[Task]

    add_fields = task_admin.get_readonly_fields(request, obj=None)
    first_change_fields = task_admin.get_readonly_fields(request, obj=task)
    second_change_fields = task_admin.get_readonly_fields(request, obj=task)

    assert "creator" not in add_fields
    assert first_change_fields.count("creator") == 1
    assert second_change_fields.count("creator") == 1
    assert "created_at" in add_fields
    assert "updated_at" in add_fields
    assert "creator" not in task_admin.readonly_fields


def test_admin_form_reports_ineligible_readonly_creator_as_non_field_error(
    user_factory,
):
    admin_user = user_factory("admin", is_staff=True, is_superuser=True)
    owner = user_factory("owner")
    creator = user_factory("creator")
    project = Project.objects.create(name="Platform migration", owner=owner)
    membership = ProjectMembership.objects.create(project=project, user=creator)
    task = Task.objects.create(
        project=project,
        title="Plan rollout",
        creator=creator,
        assignee=owner,
    )
    membership.delete()
    request = RequestFactory().post("/admin/tasks/task/")
    request.user = admin_user
    task_admin = admin.site._registry[Task]
    form_class = task_admin.get_form(request, obj=task)
    form = form_class(
        data={
            "project": project.pk,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "assignee": owner.pk,
            "due_date": "",
        },
        instance=task,
    )

    assert form.is_valid() is False
    assert NON_FIELD_ERRORS in form.errors
