from django.shortcuts import render
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters import rest_framework as django_filters
from datetime import datetime
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .models import Trip, City
from .serializers import TripListSerializer, TripDetailSerializer, TripCreateUpdateSerializer
from ..seat.models import TripSeat


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

    @swagger_auto_schema(
        operation_description="Получение списка доступных поездок с возможностью фильтрации по множеству параметров",
        operation_summary="Список поездок",
        manual_parameters=[
            openapi.Parameter('origin', openapi.IN_QUERY, description="ID города отправления",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('destination', openapi.IN_QUERY, description="ID города назначения",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('date', openapi.IN_QUERY, description="Дата поездки (YYYY-MM-DD)",
                              type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Минимальная цена билета",
                              type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Максимальная цена билета",
                              type=openapi.TYPE_NUMBER),
            openapi.Parameter('vehicle__vehicle_type', openapi.IN_QUERY,
                              description="Тип транспорта (bus, minibus, car и т.д.)", type=openapi.TYPE_STRING),
            openapi.Parameter('vehicle__is_comfort', openapi.IN_QUERY, description="Повышенный комфорт (true/false)",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('vehicle__air_conditioning', openapi.IN_QUERY,
                              description="Наличие кондиционера (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('vehicle__allows_pets', openapi.IN_QUERY, description="Разрешены животные (true/false)",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по названию города",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY,
                              description="Поле для сортировки (departure_time, -departure_time, default_ticket_price, -default_ticket_price, arrival_time, -arrival_time)",
                              type=openapi.TYPE_STRING)
        ],
        tags=["Поездки"]
    )
    @method_decorator(cache_page(60 * 5))  # кэш на 5 минут
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получение детальной информации о конкретной поездке, включая данные о всех местах",
        operation_summary="Детали поездки",
        tags=["Поездки"]
    )
    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создание новой поездки. Доступно только администраторам.",
        operation_summary="Создание поездки",
        tags=["Поездки"]
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # инвалидируем кэш после создания новой поездки
        cache.delete_pattern('trip_*')
        return response

    @swagger_auto_schema(
        operation_description="Обновление информации о поездке. Доступно только администраторам.",
        operation_summary="Обновление поездки",
        tags=["Поездки"]
    )
    def update(self, request, *args, **kwargs): # требует все поля для обновления
        response = super().update(request, *args, **kwargs)
        cache.delete_pattern('trip_*')
        return response

    @swagger_auto_schema(
        operation_description="Частичное обновление информации о поездке. Доступно только администраторам.",
        operation_summary="Частичное обновление поездки",
        tags=["Поездки"]
    )
    def partial_update(self, request, *args, **kwargs): # позволяет обновлять только указанные поля
        response = super().partial_update(request, *args, **kwargs)
        cache.delete_pattern('trip_*')
        return response

    @swagger_auto_schema(
        operation_description="Удаление поездки. Доступно только администраторам.",
        operation_summary="Удаление поездки",
        tags=["Поездки"]
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        cache.delete_pattern('trip_*')
        return response

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TripCreateUpdateSerializer
        elif self.action == 'retrieve':
            return TripDetailSerializer
        else:
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

    def get_queryset(self): # сюда можно добавлять фильтрации
        """Базовая фильтрация"""
        queryset = Trip.objects.select_related(
            'origin', 'destination', 'vehicle'
        )
        return queryset

    @swagger_auto_schema(
        operation_description="Получение списка городов",
        operation_summary="Список городов",
        tags=["Поездки"]
    )
    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 60))  # кэш на 1 час, так как список городов меняется редко
    def cities(self, request):
        """Получение списка городов для фильтрации"""
        cities = City.objects.all()
        return Response({
            'origin_cities': [{'id': c.id, 'name': c.name} for c in cities],
            'destination_cities': [{'id': c.id, 'name': c.name} for c in cities]
        })

    @swagger_auto_schema(
        operation_description="Получение списка свободных мест на поездке",
        operation_summary="Свободные места",
        tags=["Поездки"]
    )
    @action(detail=True, methods=['get'])
    def available_seats(self, request, pk=None):
        """Получение списка свободных мест"""
        trip = self.get_object()
        # Изменяем запрос, чтобы использовать TripSeat
        trip_seats = TripSeat.objects.filter(trip=trip, is_booked=False).select_related('seat')
        return Response({
            'available_seats': [{
                'id': trip_seat.seat.id,
                'number': trip_seat.seat.seat_number,
                'type': trip_seat.seat.seat_type
            } for trip_seat in trip_seats]
        })