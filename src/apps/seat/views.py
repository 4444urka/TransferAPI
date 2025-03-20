from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.seat.models import Seat, TripSeat
from apps.seat.serializers import SeatSerializer
from apps.vehicle.models import Vehicle


class SeatViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    ViewSet для модели Seat.

    Доступные действия:
    - list (GET): получение списка мест.
    - retrieve (GET): получение деталей конкретного места.
    - update / partial_update (PUT/PATCH): редактирование мест.
    - getSeatsByVehicle (GET): получение списка мест по ID транспортного средства.

    Создание (POST) и удаление (DELETE) отключены, так как:
    - Места создаются автоматически при создании транспортного средства (через сигналы).
    - Удаление мест разрешается только через удаление транспортного средства.
    """
    queryset = Seat.objects.all()  # Восстановленная строка с атрибутом queryset
    serializer_class = SeatSerializer

    def get_permissions(self):
        """Определение разрешений в зависимости от действия"""
        if self.action in ['update', 'partial_update']:
            return [IsAdminUser()]  # Только администраторы могут изменять места
        return super().get_permissions()

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
        operation_description="Полное обновление информации о месте (только разрешенные поля)",
        operation_summary="Обновление места",
        tags=["Места"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_booked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус бронирования места'),
                'seat_type': openapi.Schema(type=openapi.TYPE_STRING, description='Тип места (front, middle, back)')
            }
        )
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление информации о месте (только разрешенные поля)",
        operation_summary="Частичное обновление места",
        tags=["Места"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_booked': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Статус бронирования места'),
                'seat_type': openapi.Schema(type=openapi.TYPE_STRING, description='Тип места (front, middle, back)')
            }
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    # Переопределяем методы, чтобы все же получать понятные ответы даже при ручном вызове
    @swagger_auto_schema(
        operation_description="Создание нового места (запрещено)",
        operation_summary="Создание места",
        tags=["Места"]
    )
    def create(self, request, *args, **kwargs):
        # Запрещаем создание мест через API
        return Response(
            {"detail": "Создание мест через API запрещено"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @swagger_auto_schema(
        operation_description="Удаление места (запрещено)",
        operation_summary="Удаление места",
        tags=["Места"]
    )
    def destroy(self, request, *args, **kwargs):
        # Запрещаем удаление мест через API
        return Response(
            {"detail": "Удаление мест через API запрещено"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

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
        """Получение списка мест для конкретного транспортного средства"""
        try:
            # Проверяем существование транспортного средства
            vehicle = Vehicle.objects.get(pk=vehicle_id)

            # Получаем места для этого транспортного средства
            seats = Seat.objects.filter(vehicle=vehicle)
            serializer = self.get_serializer(seats, many=True)

            return Response(serializer.data)
        except Vehicle.DoesNotExist:
            return Response(
                {"detail": "Транспортное средство не найдено"},
                status=status.HTTP_404_NOT_FOUND
            )