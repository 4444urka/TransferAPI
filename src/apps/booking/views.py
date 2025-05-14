from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

import logging

from .permissions import HasBookingPermission
from .serializers import BookingSerializer, BookingDetailSerializer
from .services import BookingService
from apps.trip.models import Trip
from apps.seat.models import TripSeat

logger = logging.getLogger(__name__)

bookingService = BookingService

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с бронированиями.

    Обычные пользователи видят только свои бронирования.
    Администраторы имеют доступ ко всем бронированиям.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, HasBookingPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'trip']
    search_fields = ['trip__origin__name', 'trip__destination__name']
    ordering_fields = ['booking_datetime', 'trip__departure_time']
    ordering = ['-booking_datetime']

    @swagger_auto_schema(
        operation_description="Получение списка бронирований. Для обычных пользователей возвращаются только их собственные бронирования, для администраторов - все бронирования.",
        operation_summary="Список бронирований",
        manual_parameters=[
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Фильтр по статусу активности (true/false)",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('trip', openapi.IN_QUERY, description="Фильтр по ID поездки",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по названию городов",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY,
                              description="Поле для сортировки (booking_datetime, -booking_datetime, trip__departure_time, -trip__departure_time)",
                              type=openapi.TYPE_STRING)
        ],
        tags=["Бронирования"]
    )
    def list(self, request, *args, **kwargs):
        # Если запрос с параметром detailed=true, попробуем извлечь данные из кэша
        detailed = request.query_params.get('detailed', 'false').lower() in ['true', '1']
        if detailed:
            user = request.user
            cache_key = f"booking_detailed_{user.id}"
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Using cached bookings data for the user {user.id}")
                return Response(cached_data)
        else:
            logger.debug("Using non-cached bookings data")
        response = super().list(request, *args, **kwargs)
        if detailed:
            logger.debug(f"Caching booking data for the user {request.user.id}")
            cache.set(cache_key, response.data, timeout=300)
        return response

    @swagger_auto_schema(
        operation_description="Получение детальной информации о бронировании. Пользователь может видеть только свои бронирования. Администратор может видеть любое бронирование.",
        operation_summary="Детали бронирования",
        tags=["Бронирования"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создание нового бронирования. Автоматически привязывается к текущему пользователю.",
        operation_summary="Создание бронирования",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['trip_id', 'seat_numbers', 'pickup_location', 'dropoff_location'],
            properties={
                'trip_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID поездки'),
                'seat_numbers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER),
                                            description='Массив номеров мест для бронирования'),
                'pickup_location': openapi.Schema(type=openapi.TYPE_STRING, description='Адрес посадки'),
                'dropoff_location': openapi.Schema(type=openapi.TYPE_STRING, description='Адрес высадки')
            }
        ),
        tags=["Бронирования"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Полное обновление бронирования. Доступно только владельцу или администратору.",
        operation_summary="Обновление бронирования",
        tags=["Бронирования"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление бронирования. Доступно только владельцу или администратору.",
        operation_summary="Частичное обновление бронирования",
        tags=["Бронирования"]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удаление бронирования. Доступно только владельцу или администратору.",
        operation_summary="Удаление бронирования",
        tags=["Бронирования"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Получение списка бронирований с учетом прав доступа"""
        return bookingService.get_user_bookings(self.request.user)

    def get_serializer_class(self):
        """
        Используем подробный сериализатор для действий, которые требуют детальной информации,
        а для списка можем использовать более компактный вариант.
        При запросе detailed=true можно выбрать BookingDetailSerializer.
        """
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return BookingDetailSerializer
        # Если query-параметр detailed=true в списке — возвращаем подробности
        detailed = self.request.query_params.get('detailed', 'false').lower() in ['true', '1']
        if detailed:
            return BookingDetailSerializer
        return BookingSerializer

    def perform_create(self, serializer):
        """Автоматически устанавливаем текущего пользователя при создании"""
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Отменяет активное бронирование. Устанавливает флаг is_active=False и освобождает забронированные места.",
        operation_summary="Отмена бронирования",
        responses={
            200: openapi.Response(
                description="Бронирование успешно отменено",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка отмены бронирования",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
        tags=["Бронирования"]
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Эндпоинт для отмены бронирования"""
        booking = self.get_object()
        
        try:
            bookingService.cancel_booking(booking)
            return Response({"detail": "Бронирование успешно отменено"})
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_trip_seats(request):
    """
    Возвращает список TripSeat (id и строковое представление) 
    для указанного trip_id в формате JSON.
    """
    trip_id = request.GET.get('trip_id')
    data = {'seats': []} # По умолчанию пустой список

    if trip_id:
        try:
            # Проверяем, существует ли поездка
            trip = get_object_or_404(Trip, pk=trip_id)
            # Получаем все TripSeat для этой поездки
            # Возвращаем все места: и свободные, и забронированные, 
            # чтобы пользователь видел всю картину
            trip_seats = TripSeat.objects.filter(trip=trip).order_by('seat__seat_number')
            
            # Формируем список для JSON
            data['seats'] = [
                {'id': ts.pk, 'text': str(ts)}
                for ts in trip_seats
            ]
        except ValueError:
            # trip_id не является числом
            pass # Возвращаем пустой список
        # get_object_or_404 обработает случай, если Trip не найден

    return JsonResponse(data)