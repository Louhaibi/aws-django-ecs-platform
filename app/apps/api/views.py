from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import serializers, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.api.access import projects_accessible_to, user_is_project_manager
from apps.api.filters import StableOrderingFilter, TaskFilter
from apps.api.permissions import (
    ProjectMembershipPermission,
    ProjectPermission,
    TaskPermission,
)
from apps.api.serializers import (
    CurrentUserSerializer,
    ProjectMembershipCreateSerializer,
    ProjectMembershipReadSerializer,
    ProjectMembershipUpdateSerializer,
    ProjectSerializer,
    TaskCreateSerializer,
    TaskReadSerializer,
    TaskUpdateSerializer,
)
from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Task

DUPLICATE_MEMBERSHIP_MESSAGE = "A user can have only one membership in a project."


class PublicTokenObtainPairView(TokenObtainPairView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(auth=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PublicTokenRefreshView(TokenRefreshView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(auth=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PublicTokenVerifyView(TokenVerifyView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(auth=[])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PublicSchemaView(SpectacularAPIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(auth=[], responses={200: OpenApiTypes.OBJECT})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicSwaggerView(SpectacularSwaggerView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(auth=[], responses={200: OpenApiTypes.STR})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CurrentUserView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=CurrentUserSerializer)
    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


@extend_schema_view(create=extend_schema(responses={201: ProjectSerializer}))
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated, ProjectPermission)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")
    filter_backends = (SearchFilter, StableOrderingFilter)
    search_fields = ("name",)
    ordering_fields = ("name", "created_at", "updated_at")
    ordering = ("-created_at", "-id")

    def get_queryset(self):
        return projects_accessible_to(self.request.user).select_related("owner")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema_view(
    create=extend_schema(responses={201: ProjectMembershipReadSerializer}),
    partial_update=extend_schema(responses=ProjectMembershipReadSerializer),
)
class ProjectMembershipViewSet(viewsets.ModelViewSet):
    queryset = ProjectMembership.objects.all()
    permission_classes = (IsAuthenticated, ProjectMembershipPermission)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")
    filter_backends = (DjangoFilterBackend, StableOrderingFilter)
    filterset_fields = ("project", "role")
    ordering_fields = ("created_at", "role")
    ordering = ("-created_at", "-id")

    def get_queryset(self):
        accessible_projects = projects_accessible_to(self.request.user)
        return ProjectMembership.objects.filter(
            project_id__in=accessible_projects.values("pk")
        ).select_related("project", "project__owner", "user")

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectMembershipCreateSerializer
        if self.action == "partial_update":
            return ProjectMembershipUpdateSerializer
        return ProjectMembershipReadSerializer

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        user = serializer.validated_data["user"]
        if project.owner_id != self.request.user.pk:
            raise PermissionDenied("Only the project owner can manage memberships.")

        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as error:
            duplicate_now_exists = ProjectMembership.objects.filter(
                project_id=project.pk,
                user_id=user.pk,
            ).exists()
            if duplicate_now_exists:
                raise serializers.ValidationError(
                    {"non_field_errors": [DUPLICATE_MEMBERSHIP_MESSAGE]}
                ) from error
            raise


@extend_schema_view(
    create=extend_schema(responses={201: TaskReadSerializer}),
    partial_update=extend_schema(responses=TaskReadSerializer),
)
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    permission_classes = (IsAuthenticated, TaskPermission)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")
    filter_backends = (DjangoFilterBackend, SearchFilter, StableOrderingFilter)
    filterset_class = TaskFilter
    search_fields = ("title", "description")
    ordering_fields = ("title", "due_date", "created_at", "updated_at")
    ordering = ("-created_at", "-id")

    def get_queryset(self):
        accessible_projects = projects_accessible_to(self.request.user)
        return Task.objects.filter(
            project_id__in=accessible_projects.values("pk")
        ).select_related("project", "project__owner", "creator", "assignee")

    def get_serializer_class(self):
        if self.action == "create":
            return TaskCreateSerializer
        if self.action == "partial_update":
            return TaskUpdateSerializer
        return TaskReadSerializer

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if not user_is_project_manager(self.request.user, project):
            raise PermissionDenied("Only project owners and managers can create tasks.")
        serializer.save(creator=self.request.user)
