import pytest
from django.contrib import admin
from django.test import RequestFactory

from apps.projects.admin import ProjectAdmin, ProjectMembershipInline
from apps.projects.models import Project, ProjectMembership

pytestmark = pytest.mark.django_db


def test_project_models_are_registered_with_admin():
    assert admin.site.is_registered(Project)
    assert admin.site.is_registered(ProjectMembership)


def test_project_admin_configuration():
    project_admin = admin.site._registry[Project]
    membership_admin = admin.site._registry[ProjectMembership]

    assert isinstance(project_admin, ProjectAdmin)
    assert ProjectMembershipInline in project_admin.inlines
    assert "owner" in project_admin.autocomplete_fields
    assert "role" in membership_admin.list_filter
    assert membership_admin.autocomplete_fields == ("project", "user")


def test_project_owner_is_readonly_only_on_change(user_factory):
    request = RequestFactory().get("/admin/")
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)
    project_admin = admin.site._registry[Project]

    add_fields = project_admin.get_readonly_fields(request, obj=None)
    first_change_fields = project_admin.get_readonly_fields(request, obj=project)
    second_change_fields = project_admin.get_readonly_fields(request, obj=project)

    assert "owner" not in add_fields
    assert first_change_fields.count("owner") == 1
    assert second_change_fields.count("owner") == 1
    assert "created_at" in add_fields
    assert "updated_at" in add_fields
    assert "owner" not in project_admin.readonly_fields
