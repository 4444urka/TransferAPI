from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Booking
from .serializers import BookingSerializer, BookingDetailSerializer
from apps.seat.models import Seat
from apps.payment.models import Payment


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Пользователь может видеть только свои бронирования,
    кроме администраторов, которые видят всё
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с бронированиями.

    Обычные пользователи видят только свои бронирования.
    Администраторы имеют доступ ко всем бронированиям.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
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
            openapi.Parameter('trip', openapi.IN_QUERY, description="Фильтр по ID поездки", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по названию городов",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY,
                              description="Поле для сортировки (booking_datetime, -booking_datetime, trip__departure_time, -trip__departure_time)",
                              type=openapi.TYPE_STRING)
        ],
        tags=["Бронирования"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
            required=['trip_id', 'seats_ids', 'pickup_location', 'dropoff_location'],
            properties={
                'trip_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID поездки'),
                'seats_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER),
                                            description='Массив ID мест для бронирования'),
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
        """Пользователи видят только свои бронирования, администраторы - все"""
        # Проверяем, вызывается ли метод для генерации схемы Swagger
        if getattr(self, 'swagger_fake_view', False):
            # Для генерации схемы возвращаем базовый queryset без фильтрации
            return Booking.objects.none()

        # Обычная логика для реальных запросов
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Используем разные сериализаторы для списка и деталей"""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
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

        if not booking.is_active:
            return Response(
                {"detail": "Бронирование уже отменено"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Отмечаем бронирование как неактивное
        booking.is_active = False
        booking.save()

        # Освобождаем места
        for trip_seat in booking.trip_seats.all():
            trip_seat.is_booked = False
            trip_seat.save()

        return Response({"detail": "Бронирование успешно отменено"})