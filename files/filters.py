import django_filters
from django.db.models import Q
from django_filters.rest_framework import FilterSet

from files.models import File


class FileListFilter(FilterSet):

    search = django_filters.CharFilter(
        method='search_filter',
        label = 'Search',
        help_text = 'Search by name or folder name'
    )


    class Meta:
        model = File
        fields = {
            'name': ['icontains'],
            'folder__name': ['icontains'],
        }

    def search_filter(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value) |
            Q(folder__name__icontains=value)
        )