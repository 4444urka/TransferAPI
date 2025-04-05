from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as django_filters
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .filters import TripFilter
from .models import Trip, City
from .permissions import HasTripPermission
from .serializers import TripListSerializer, TripDetailSerializer, TripCreateUpdateSerializer
from apps.seat.models import TripSeat
from apps.seat.services.trip_seat_service import TripSeatService

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
    permission_classes = [IsAuthenticated, HasTripPermission]
    ordering_fields = ['departure_time', 'arrival_time', 'default_ticket_price']
    ordering = ['departure_time']

    trip_seat_service = TripSeatService()

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
                              type=openapi.TYPE_STRING),
            openapi.Parameter('current', openapi.IN_QUERY, 
                              description="Флаг для фильтрации актуальных поездок (true/false). Если true, возвращаются только поездки, у которых departure_time >= текущему времени.",
                              type=openapi.TYPE_BOOLEAN),
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
        Определяет разрешения для различных действий:
        - Просмотр доступен всем
        - Создание/изменение/удаление требуют соответствующих прав
        """
        return [HasTripPermission()]

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
    def seats(self, request, pk=None):
        """Получение списка всех мест в поездке (и занятых, и свободных)"""
        trip = self.get_object()
        seats_data = self.trip_seat_service.get_seats_list(trip)

        return Response({
            'seats': seats_data
        })
