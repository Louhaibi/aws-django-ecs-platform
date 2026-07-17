from django.contrib import admin

from .models import Project, ProjectMembership


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0
    fields = ("user", "role", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at", "updated_at")
    search_fields = ("name", "description", "owner__username", "owner__email")
    ordering = ("-created_at",)
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("owner",)
    inlines = (ProjectMembershipInline,)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = tuple(super().get_readonly_fields(request, obj))
        if obj is None:
            return readonly_fields
        return (*readonly_fields, "owner")


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("project__name", "user__username", "user__email")
    ordering = ("-created_at",)
    autocomplete_fields = ("project", "user")
    readonly_fields = ("created_at",)
    list_select_related = ("project", "user")
