import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.projects.models import Project, ProjectMembership

pytestmark = pytest.mark.django_db


def test_project_creation_accepts_initial_owner(user_factory):
    owner = user_factory("owner")

    project = Project.objects.create(name="Platform migration", owner=owner)

    assert project.pk is not None
    assert project.owner == owner
    assert project.description == ""
    assert project.created_at is not None
    assert project.updated_at is not None


def test_project_owner_cannot_be_changed(user_factory):
    owner = user_factory("owner")
    replacement = user_factory("replacement")
    project = Project.objects.create(name="Platform migration", owner=owner)

    project.owner = replacement

    with pytest.raises(ValidationError) as exc_info:
        project.save()

    assert "owner" in exc_info.value.message_dict
    project.refresh_from_db()
    assert project.owner == owner


def test_project_access_rejects_missing_anonymous_and_unsaved_users(
    user_factory,
    django_user_model,
):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)

    assert project.is_accessible_by(None) is False
    assert project.is_accessible_by(AnonymousUser()) is False
    assert project.is_accessible_by(django_user_model(username="unsaved")) is False


def test_project_owner_access_does_not_query_memberships(
    user_factory,
    django_assert_num_queries,
):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)

    with django_assert_num_queries(0):
        assert project.is_accessible_by(owner) is True


@pytest.mark.parametrize(
    "role",
    [ProjectMembership.Role.MEMBER, ProjectMembership.Role.MANAGER],
)
def test_project_members_have_access(user_factory, role):
    owner = user_factory(f"owner-{role}")
    member = user_factory(f"member-{role}")
    unrelated = user_factory(f"unrelated-{role}")
    project = Project.objects.create(name=f"Project {role}", owner=owner)
    ProjectMembership.objects.create(project=project, user=member, role=role)

    assert project.is_accessible_by(member) is True
    assert project.is_accessible_by(unrelated) is False


def test_duplicate_membership_is_rejected_by_model_validation(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    ProjectMembership.objects.create(project=project, user=member)

    with pytest.raises(ValidationError) as exc_info:
        ProjectMembership.objects.create(project=project, user=member)

    assert NON_FIELD_ERRORS in exc_info.value.message_dict


def test_duplicate_membership_is_rejected_by_database_constraint(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    ProjectMembership.objects.create(project=project, user=member)

    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectMembership.objects.bulk_create(
            [ProjectMembership(project=project, user=member)]
        )


def test_project_owner_cannot_have_membership(user_factory):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)

    with pytest.raises(ValidationError) as exc_info:
        ProjectMembership.objects.create(project=project, user=owner)

    assert "user" in exc_info.value.message_dict


def test_invalid_membership_role_is_rejected_by_database_constraint(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)

    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectMembership.objects.bulk_create(
            [ProjectMembership(project=project, user=member, role="invalid")]
        )


def test_project_and_membership_string_representations(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    membership = ProjectMembership.objects.create(
        project=project,
        user=member,
        role=ProjectMembership.Role.MANAGER,
    )

    assert str(project) == "Platform migration"
    assert str(membership) == "member - Platform migration (Manager)"


def test_project_deletion_cascades_memberships(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    membership = ProjectMembership.objects.create(project=project, user=member)

    project.delete()

    assert not ProjectMembership.objects.filter(pk=membership.pk).exists()


def test_project_owner_deletion_is_protected(user_factory):
    owner = user_factory("owner")
    Project.objects.create(name="Platform migration", owner=owner)

    with pytest.raises(ProtectedError):
        owner.delete()
