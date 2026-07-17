from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.projects.models import Project


def _add_validation_error(errors, field_name, error, excluded_fields):
    error_key = (
        NON_FIELD_ERRORS
        if excluded_fields and field_name in excluded_fields
        else field_name
    )
    errors.setdefault(error_key, []).append(error)


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", _("To do")
        IN_PROGRESS = "in_progress", _("In progress")
        DONE = "done", _("Done")
        CANCELLED = "cancelled", _("Cancelled")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.TODO)
    priority = models.CharField(
        max_length=10,
        choices=Priority,
        default=Priority.MEDIUM,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    status__in=("todo", "in_progress", "done", "cancelled")
                ),
                name="tasks_task_valid_status",
                violation_error_code="invalid_task_status",
                violation_error_message="Task status is not supported.",
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=("low", "medium", "high", "urgent")),
                name="tasks_task_valid_priority",
                violation_error_code="invalid_task_priority",
                violation_error_message="Task priority is not supported.",
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.project}"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        errors = {}

        if self.pk is not None:
            persisted_creator_id = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("creator_id", flat=True)
                .first()
            )
            if (
                persisted_creator_id is not None
                and persisted_creator_id != self.creator_id
            ):
                _add_validation_error(
                    errors,
                    "creator",
                    ValidationError(
                        _("Task creator cannot be changed after creation."),
                        code="immutable",
                    ),
                    exclude,
                )

        project = self._state.fields_cache.get("project")
        if project is None and self.project_id is not None:
            project = Project.objects.filter(pk=self.project_id).first()

        if project is not None and self.creator_id is not None:
            creator = self._state.fields_cache.get("creator")
            if creator is None:
                creator = self.creator
            if not project.is_accessible_by(creator):
                _add_validation_error(
                    errors,
                    "creator",
                    ValidationError(
                        _("Task creator must have access to the project."),
                        code="creator_without_access",
                    ),
                    exclude,
                )

        if project is not None and self.assignee_id is not None:
            assignee = self._state.fields_cache.get("assignee")
            if assignee is None:
                assignee = self.assignee
            if not project.is_accessible_by(assignee):
                _add_validation_error(
                    errors,
                    "assignee",
                    ValidationError(
                        _("Task assignee must be the project owner or a member."),
                        code="assignee_without_access",
                    ),
                    exclude,
                )

        if errors:
            raise ValidationError(errors)
