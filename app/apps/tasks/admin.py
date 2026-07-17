from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "status",
        "priority",
        "assignee",
        "creator",
        "due_date",
        "updated_at",
    )
    list_filter = ("status", "priority", "due_date", "created_at")
    search_fields = (
        "title",
        "description",
        "project__name",
        "assignee__username",
        "creator__username",
    )
    ordering = ("-created_at",)
    autocomplete_fields = ("project", "assignee", "creator")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("project", "assignee", "creator")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = tuple(super().get_readonly_fields(request, obj))
        if obj is None:
            return readonly_fields
        return (*readonly_fields, "creator")
