from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.api.views import (
    CurrentUserView,
    ProjectMembershipViewSet,
    ProjectViewSet,
    PublicTokenObtainPairView,
    PublicTokenRefreshView,
    PublicTokenVerifyView,
    TaskViewSet,
)

router = SimpleRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("memberships", ProjectMembershipViewSet, basename="membership")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("auth/token/", PublicTokenObtainPairView.as_view(), name="token-obtain"),
    path(
        "auth/token/refresh/",
        PublicTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "auth/token/verify/",
        PublicTokenVerifyView.as_view(),
        name="token-verify",
    ),
    path("users/me/", CurrentUserView.as_view(), name="current-user"),
    path("", include(router.urls)),
]
