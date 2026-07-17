from django.contrib.auth import get_user_model
from django.core.exceptions import (
    NON_FIELD_ERRORS,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import serializers
from rest_framework.settings import api_settings

from apps.api.access import projects_accessible_to
from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Task


def _raise_api_validation_error(error):
    if hasattr(error, "message_dict"):
        details = {}
        for field, messages in error.message_dict.items():
            key = (
                api_settings.NON_FIELD_ERRORS_KEY
                if field == NON_FIELD_ERRORS
                else field
            )
            details[key] = messages
        raise serializers.ValidationError(details) from error

    raise serializers.ValidationError(
        {api_settings.NON_FIELD_ERRORS_KEY: error.messages}
    ) from error


def _reject_submitted_fields(serializer, field_names):
    errors = {
        field_name: "This field cannot be set through this operation."
        for field_name in field_names
        if field_name in serializer.initial_data
    }
    if errors:
        raise serializers.ValidationError(errors)


class ModelValidationErrorMixin:
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as error:
            _raise_api_validation_error(error)

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as error:
            _raise_api_validation_error(error)


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = fields


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "first_name", "last_name")
        read_only_fields = fields


class ProjectSerializer(ModelValidationErrorMixin, serializers.ModelSerializer):
    owner = UserSummarySerializer(read_only=True)

    class Meta:
        model = Project
        fields = ("id", "name", "description", "owner", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "created_at", "updated_at")

    def validate(self, attrs):
        _reject_submitted_fields(self, ("owner",))
        return super().validate(attrs)


class AccessibleProjectField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get("request")
        if request is None:
            return Project.objects.none()
        return projects_accessible_to(request.user)


class ProjectMembershipReadSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    user_summary = UserSummarySerializer(source="user", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = (
            "id",
            "project",
            "project_name",
            "user",
            "user_summary",
            "role",
            "created_at",
        )
        read_only_fields = fields


class ProjectMembershipCreateSerializer(
    ModelValidationErrorMixin,
    serializers.ModelSerializer,
):
    project = AccessibleProjectField()
    project_name = serializers.CharField(source="project.name", read_only=True)
    user_summary = UserSummarySerializer(source="user", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = (
            "id",
            "project",
            "project_name",
            "user",
            "user_summary",
            "role",
            "created_at",
        )
        read_only_fields = ("id", "project_name", "user_summary", "created_at")
        validators = ()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if ProjectMembership.objects.filter(
            project=attrs["project"],
            user=attrs["user"],
        ).exists():
            raise serializers.ValidationError(
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        "A user can have only one membership in a project."
                    ]
                }
            )
        return attrs


class ProjectMembershipUpdateSerializer(
    ModelValidationErrorMixin,
    serializers.ModelSerializer,
):
    project_name = serializers.CharField(source="project.name", read_only=True)
    user_summary = UserSummarySerializer(source="user", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = (
            "id",
            "project",
            "project_name",
            "user",
            "user_summary",
            "role",
            "created_at",
        )
        read_only_fields = (
            "id",
            "project",
            "project_name",
            "user",
            "user_summary",
            "created_at",
        )

    def validate(self, attrs):
        _reject_submitted_fields(self, ("project", "user"))
        return super().validate(attrs)


class TaskReadSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_summary = UserSummarySerializer(source="assignee", read_only=True)
    creator_summary = UserSummarySerializer(source="creator", read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_summary",
            "due_date",
            "creator",
            "creator_summary",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class TaskCreateSerializer(ModelValidationErrorMixin, serializers.ModelSerializer):
    project = AccessibleProjectField()
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_summary = UserSummarySerializer(source="assignee", read_only=True)
    creator_summary = UserSummarySerializer(source="creator", read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_summary",
            "due_date",
            "creator",
            "creator_summary",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "project_name",
            "assignee_summary",
            "creator",
            "creator_summary",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        _reject_submitted_fields(self, ("creator",))
        return super().validate(attrs)


class TaskUpdateSerializer(ModelValidationErrorMixin, serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee_summary = UserSummarySerializer(source="assignee", read_only=True)
    creator_summary = UserSummarySerializer(source="creator", read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_summary",
            "due_date",
            "creator",
            "creator_summary",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "project",
            "project_name",
            "creator",
            "creator_summary",
            "assignee_summary",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        _reject_submitted_fields(self, ("project", "creator"))
        return super().validate(attrs)
