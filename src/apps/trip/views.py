from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters import rest_framework as django_filters
from datetime import datetime

from .models import Trip, City
from .serializers import TripListSerializer, TripDetailSerializer

class TripFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="default_ticket_price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="default_ticket_price", lookup_expr='lte')
    date = django_filters.DateFilter(field_name="departure_time", lookup_expr='date')
    departure_after = django_filters.DateTimeFilter(field_name="departure_time", lookup_expr='gte')
    departure_before = django_filters.DateTimeFilter(field_name="departure_time", lookup_expr='lte')
    
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

class TripViewSet(viewsets.ModelViewSet):
    """
    API для работы с поездками.
    
    list: Получение списка поездок с фильтрацией
    retrieve: Получение детальной информации о поездке
    create: Создание новой поездки (только для админов)
    update: Обновление поездки (только для админов)
    destroy: Удаление поездки (только для админов)
    """
    queryset = Trip.objects.all()
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = TripFilter
    search_fields = ['origin__name', 'destination__name']
    ordering_fields = ['departure_time', 'arrival_time', 'default_ticket_price']
    ordering = ['departure_time']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TripDetailSerializer
        return TripListSerializer

    def get_permissions(self):
        """
        - Просмотр доступен всем
        - Создание/изменение/удаление только админам
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Базовая фильтрация"""
        queryset = Trip.objects.select_related(
            'origin', 'destination', 'vehicle'
        ).filter(
            departure_time__gte=timezone.now()
        )
        return queryset

    @action(detail=False, methods=['get'])
    def cities(self, request):
        """Получение списка городов для фильтрации"""
        cities = City.objects.all()
        return Response({
            'origin_cities': [{'id': c.id, 'name': c.name} for c in cities],
            'destination_cities': [{'id': c.id, 'name': c.name} for c in cities]
        })

    @action(detail=True, methods=['get'])
    def available_seats(self, request, pk=None):
        """Получение списка свободных мест"""
        trip = self.get_object()
        seats = trip.vehicle.seat_set.filter(is_booked=False)
        return Response({
            'available_seats': [{
                'id': seat.id,
                'number': seat.seat_number,
                'type': seat.seat_type
            } for seat in seats]
        })
