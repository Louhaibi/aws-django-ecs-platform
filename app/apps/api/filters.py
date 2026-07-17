from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from apps.tasks.models import Task


class TaskFilter(filters.FilterSet):
    due_date_after = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_date_before = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    unassigned = filters.BooleanFilter(field_name="assignee", lookup_expr="isnull")

    class Meta:
        model = Task
        fields = (
            "project",
            "status",
            "priority",
            "assignee",
            "due_date",
        )


class StableOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ordering

        ordering = list(ordering)
        if "id" not in {field.removeprefix("-") for field in ordering}:
            ordering.append("id")
        return ordering
