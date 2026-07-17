import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Task

pytestmark = pytest.mark.django_db


def test_task_creation_accepts_initial_creator_and_defaults(user_factory):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)

    task = Task.objects.create(
        project=project,
        title="Configure health checks",
        creator=owner,
    )

    assert task.pk is not None
    assert task.creator == owner
    assert task.status == Task.Status.TODO
    assert task.priority == Task.Priority.MEDIUM
    assert task.assignee is None
    assert task.due_date is None
    assert task.description == ""
    assert task.created_at is not None
    assert task.updated_at is not None


def test_task_creator_cannot_be_changed(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    ProjectMembership.objects.create(project=project, user=member)
    task = Task.objects.create(project=project, title="Plan rollout", creator=owner)

    task.creator = member

    with pytest.raises(ValidationError) as exc_info:
        task.save()

    assert "creator" in exc_info.value.message_dict
    task.refresh_from_db()
    assert task.creator == owner


def test_owner_is_valid_task_assignee(user_factory):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)

    task = Task.objects.create(
        project=project,
        title="Plan rollout",
        creator=owner,
        assignee=owner,
    )

    assert task.assignee == owner


@pytest.mark.parametrize(
    "role",
    [ProjectMembership.Role.MEMBER, ProjectMembership.Role.MANAGER],
)
def test_project_member_is_valid_task_creator_and_assignee(user_factory, role):
    owner = user_factory(f"owner-{role}")
    member = user_factory(f"member-{role}")
    project = Project.objects.create(name=f"Project {role}", owner=owner)
    ProjectMembership.objects.create(project=project, user=member, role=role)

    task = Task.objects.create(
        project=project,
        title=f"Task {role}",
        creator=member,
        assignee=member,
    )

    assert task.creator == member
    assert task.assignee == member


def test_unrelated_task_creator_is_rejected(user_factory):
    owner = user_factory("owner")
    unrelated = user_factory("unrelated")
    project = Project.objects.create(name="Platform migration", owner=owner)

    with pytest.raises(ValidationError) as exc_info:
        Task.objects.create(
            project=project,
            title="Plan rollout",
            creator=unrelated,
        )

    assert "creator" in exc_info.value.message_dict


def test_unrelated_task_assignee_is_rejected(user_factory):
    owner = user_factory("owner")
    unrelated = user_factory("unrelated")
    project = Project.objects.create(name="Platform migration", owner=owner)

    with pytest.raises(ValidationError) as exc_info:
        Task.objects.create(
            project=project,
            title="Plan rollout",
            creator=owner,
            assignee=unrelated,
        )

    assert "assignee" in exc_info.value.message_dict


def test_task_can_be_unassigned_without_due_date(user_factory):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)

    task = Task.objects.create(project=project, title="Plan rollout", creator=owner)

    assert task.assignee is None
    assert task.due_date is None


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [("status", "invalid"), ("priority", "invalid")],
)
def test_task_choices_are_rejected_by_database_constraints(
    user_factory,
    field,
    invalid_value,
):
    owner = user_factory(f"owner-{field}")
    project = Project.objects.create(name=f"Project {field}", owner=owner)
    values = {
        "project": project,
        "title": f"Invalid {field}",
        "creator": owner,
        field: invalid_value,
    }

    with pytest.raises(IntegrityError), transaction.atomic():
        Task.objects.bulk_create([Task(**values)])


def test_membership_deletion_does_not_rewrite_historical_task(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    membership = ProjectMembership.objects.create(project=project, user=member)
    task = Task.objects.create(
        project=project,
        title="Plan rollout",
        creator=member,
        assignee=member,
    )

    membership.delete()
    task.refresh_from_db()

    assert task.creator_id == member.pk
    assert task.assignee_id == member.pk


def test_former_member_assignee_must_be_cleared_or_replaced(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    membership = ProjectMembership.objects.create(project=project, user=member)
    task = Task.objects.create(
        project=project,
        title="Plan rollout",
        creator=owner,
        assignee=member,
    )
    membership.delete()

    with pytest.raises(ValidationError) as exc_info:
        task.save()

    assert "assignee" in exc_info.value.message_dict

    task.assignee = None
    task.save()
    task.refresh_from_db()
    assert task.assignee is None


def test_former_member_creator_requires_restored_access(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    membership = ProjectMembership.objects.create(project=project, user=member)
    task = Task.objects.create(
        project=project,
        title="Plan rollout",
        creator=member,
        assignee=owner,
    )
    membership.delete()

    with pytest.raises(ValidationError) as exc_info:
        task.save()

    assert "creator" in exc_info.value.message_dict

    ProjectMembership.objects.create(project=project, user=member)
    task.save()


def test_task_string_representation(user_factory):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)
    task = Task.objects.create(
        project=project,
        title="Configure health checks",
        creator=owner,
    )

    assert str(task) == "Configure health checks - Platform migration"


def test_deleting_assignee_unassigns_task(user_factory):
    owner = user_factory("owner")
    member = user_factory("member")
    project = Project.objects.create(name="Platform migration", owner=owner)
    ProjectMembership.objects.create(project=project, user=member)
    task = Task.objects.create(
        project=project,
        title="Plan rollout",
        creator=owner,
        assignee=member,
    )

    member.delete()
    task.refresh_from_db()

    assert task.assignee is None


def test_deleting_task_creator_is_protected(user_factory):
    owner = user_factory("owner")
    creator = user_factory("creator")
    project = Project.objects.create(name="Platform migration", owner=owner)
    ProjectMembership.objects.create(project=project, user=creator)
    Task.objects.create(project=project, title="Plan rollout", creator=creator)

    with pytest.raises(ProtectedError):
        creator.delete()


def test_deleting_project_cascades_tasks(user_factory):
    owner = user_factory("owner")
    project = Project.objects.create(name="Platform migration", owner=owner)
    task = Task.objects.create(project=project, title="Plan rollout", creator=owner)

    project.delete()

    assert not Task.objects.filter(pk=task.pk).exists()
