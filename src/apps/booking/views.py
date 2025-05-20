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
from django.core.exceptions import ValidationError

import logging

from .permissions import HasBookingPermission
from .serializers import BookingDetailSerializer
from .services import BookingService
from apps.trip.models import Trip
from apps.seat.models import TripSeat
from .models import Booking

logger = logging.getLogger(__name__)

bookingService = BookingService

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с бронированиями.

    Обычные пользователи видят только свои бронирования.
    Администраторы имеют доступ ко всем бронированиям.
    """
    serializer_class = BookingDetailSerializer
    permission_classes = [IsAuthenticated, HasBookingPermission]
    http_method_names = ['get', 'post', 'delete']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['trip', 'is_active']
    search_fields = ['trip__from_city__name', 'trip__to_city__name']
    ordering_fields = ['booking_datetime', 'trip__departure_time', 'trip__arrival_time']
    ordering = ['-booking_datetime']

    @swagger_auto_schema(
        operation_description="Получение списка бронирований с полными данными о поездке, пользователе и платеже. Для обычных пользователей возвращаются только их собственные бронирования, для администраторов - все бронирования.",
        operation_summary="Список бронирований",
        manual_parameters=[
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Фильтр по статусу активности", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('trip', openapi.IN_QUERY, description="Фильтр по ID поездки", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по названию города", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Сортировка (например, -booking_datetime)", type=openapi.TYPE_STRING),
        ],
        tags=["Бронирования"]
    )
    def get_queryset(self):
        queryset = Booking.objects.select_related('user', 'trip', 'payment').prefetch_related('trip_seats__seat')
        
        # Добавляем специальную обработку для параметра is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            # Преобразуем строковое значение в булево
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Если пользователь не имеет права просматривать все бронирования,
        # фильтруем только его бронирования
        if not self.request.user.has_perm('booking.can_view_all_booking') and not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Добавляем отдельную обработку для параметра trip
        trip = self.request.query_params.get('trip')
        if trip is not None:
            queryset = queryset.filter(trip_id=trip)
            
        return queryset

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

    def get_serializer_class(self):
        """
        Используем BookingDetailSerializer для всех операций.
        """
        return BookingDetailSerializer
        
    def get_serializer(self, *args, **kwargs):
        """
        Переопределяем метод get_serializer для списка бронирований,
        чтобы всегда возвращались сериализованные вложенные объекты.
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

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
        booking = self.get_object()
        
        # Проверка, является ли пользователь владельцем бронирования
        if booking.user != request.user and not request.user.is_staff:
            return Response({"error": "Вы не можете отменить чужое бронирование"}, status=status.HTTP_403_FORBIDDEN)
        
        # Проверка, активно ли бронирование
        if not booking.is_active:
            return Response({"error": "Бронирование уже отменено"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Отмена бронирования
        try:
            BookingService.cancel_booking(booking)
            return Response({"message": "Бронирование успешно отменено"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error canceling booking: {e}")
            return Response({"error": f"Ошибка при отмене бронирования: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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