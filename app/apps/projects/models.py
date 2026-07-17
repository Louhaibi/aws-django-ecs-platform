from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)

        if self.pk is None:
            return

        persisted_owner_id = (
            type(self)
            .objects.filter(pk=self.pk)
            .values_list("owner_id", flat=True)
            .first()
        )
        if persisted_owner_id is None or persisted_owner_id == self.owner_id:
            return

        error = ValidationError(
            _("Project owner cannot be changed after creation."),
            code="immutable",
        )
        if exclude and "owner" in exclude:
            raise ValidationError({NON_FIELD_ERRORS: error})
        raise ValidationError({"owner": error})

    def is_accessible_by(self, user):
        if (
            user is None
            or not getattr(user, "is_authenticated", False)
            or user.pk is None
        ):
            return False

        if user.pk == self.owner_id:
            return True

        if self.pk is None:
            return False

        return self.memberships.filter(user_id=user.pk).exists()


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", _("Member")
        MANAGER = "manager", _("Manager")

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(max_length=20, choices=Role, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("project", "user"),
                name="projects_projectmembership_unique_project_user",
                violation_error_code="duplicate_membership",
                violation_error_message=(
                    "A user can have only one membership in a project."
                ),
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=("member", "manager")),
                name="projects_projectmembership_valid_role",
                violation_error_code="invalid_membership_role",
                violation_error_message="Membership role is not supported.",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.project} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()

        project = self._state.fields_cache.get("project")
        if project is not None:
            owner_id = project.owner_id
        elif self.project_id is not None:
            owner_id = (
                Project.objects.filter(pk=self.project_id)
                .values_list("owner_id", flat=True)
                .first()
            )
        else:
            owner_id = None

        if owner_id is not None and owner_id == self.user_id:
            raise ValidationError(
                {
                    "user": ValidationError(
                        _("The project owner cannot have a membership."),
                        code="owner_membership",
                    )
                }
            )
