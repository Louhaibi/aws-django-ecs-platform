from django.db.models import Q

from apps.projects.models import Project, ProjectMembership


def projects_accessible_to(user):
    if user is None or not getattr(user, "is_authenticated", False) or user.pk is None:
        return Project.objects.none()

    return Project.objects.filter(
        Q(owner_id=user.pk) | Q(memberships__user_id=user.pk)
    ).distinct()


def user_is_project_owner(user, project):
    return (
        user is not None
        and getattr(user, "is_authenticated", False)
        and user.pk is not None
        and project.owner_id == user.pk
    )


def user_is_project_manager(user, project):
    if user_is_project_owner(user, project):
        return True

    if user is None or not getattr(user, "is_authenticated", False) or user.pk is None:
        return False

    return ProjectMembership.objects.filter(
        project_id=project.pk,
        user_id=user.pk,
        role=ProjectMembership.Role.MANAGER,
    ).exists()
