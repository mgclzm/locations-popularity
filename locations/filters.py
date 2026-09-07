import django_filters

from .models import Location


class LocationFilter(django_filters.FilterSet):
    rating_min = django_filters.NumberFilter(field_name="avg_rating", lookup_expr="gte")
    category = django_filters.NumberFilter(field_name="category_id")
    author = django_filters.NumberFilter(field_name="author_id")

    class Meta:
        model = Location
        fields = ["category", "author", "rating_min"]
