from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.api.access import user_is_project_manager, user_is_project_owner


class ProjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return user_is_project_owner(request.user, obj)


class ProjectMembershipPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return user_is_project_owner(request.user, obj.project)


class TaskPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return user_is_project_owner(request.user, obj.project)
        return user_is_project_manager(request.user, obj.project)
