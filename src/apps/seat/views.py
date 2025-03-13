# apps/seat/views.py

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
from apps.seat.models import Seat
from apps.seat.serializers import SeatSerializer
from apps.vehicle.models import Vehicle

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class SeatViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """ViewSet для модели Seat."""

    @swagger_auto_schema(
        operation_description="Получение списка всех мест",
        operation_summary="Список всех мест",
        tags=["Места"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получение информации о конкретном месте",
        operation_summary="Детали места",
        tags=["Места"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получение списка мест для конкретного транспортного средства",
        operation_summary="Места транспортного средства",
        manual_parameters=[
            openapi.Parameter('vehicle_id', openapi.IN_PATH, description="ID транспортного средства",
                              type=openapi.TYPE_INTEGER)
        ],
        tags=["Места"]
    )
    @action(detail=False, methods=['get'], url_path='by_vehicle/(?P<vehicle_id>[^/.]+)')
    def get_seats_by_vehicle(self, request, vehicle_id=None):
        """Получение списка мест для конкретного транспортного средства с кэшированием"""
        # Формируем ключ кэша
        cache_key = f"seats_for_vehicle_{vehicle_id}"

        # Пытаемся получить данные из кэша
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        try:
            # Проверяем существование транспортного средства
            vehicle = Vehicle.objects.get(pk=vehicle_id)

            # Получаем места для этого транспортного средства
            seats = Seat.objects.filter(vehicle=vehicle)
            serializer = self.get_serializer(seats, many=True)

            # Кэшируем результат на 5 минут
            cache.set(cache_key, serializer.data, 300)

            return Response(serializer.data)
        except Vehicle.DoesNotExist:
            return Response(
                {"detail": "Транспортное средство не найдено"},
                status=status.HTTP_404_NOT_FOUND
            )