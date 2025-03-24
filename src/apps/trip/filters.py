import django_filters
from django.utils import timezone

from apps.trip.models import Trip


class TripFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="default_ticket_price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="default_ticket_price", lookup_expr='lte')
    date = django_filters.DateFilter(field_name="departure_time", lookup_expr='date')
    departure_after = django_filters.DateTimeFilter(field_name="departure_time", lookup_expr='gte')
    departure_before = django_filters.DateTimeFilter(field_name="departure_time", lookup_expr='lte')
    current = django_filters.BooleanFilter(method='filter_current', label='Актуальные поездки')

    def filter_current(self, queryset, name, value):
        """
        Если current=true, то возвращаем только поездки, у которых время прибытия больше или равно текущему.
        Иначе возвращаем весь queryset без дополнительной фильтрации.
        """
        if value:
            now = timezone.now()
            return queryset.filter(arrival_time__gte=now)
        return queryset

    class Meta:
        model = Trip
        fields = {
            'origin': ['exact'],
            'destination': ['exact'],
            'vehicle__vehicle_type': ['exact'],
            'vehicle__is_comfort': ['exact'],
            'vehicle__air_conditioning': ['exact'],
            'vehicle__allows_pets': ['exact'],
        }