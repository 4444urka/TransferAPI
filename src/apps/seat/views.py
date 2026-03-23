from typing import Any
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.seat.models import Seat, TripSeat
from apps.seat.permissions import HasSeatPermission
from apps.seat.serializers import SeatSerializer
from apps.vehicle.models import Vehicle
from .services.seat_service import SeatService

seat_service = SeatService()

class SeatViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    ViewSet для модели Seat с использованием сервисного слоя.

    Доступные действия:
    - list (GET): получение списка мест.
    - retrieve (GET): получение деталей конкретного места.
    - update / partial_update (PUT/PATCH): редактирование мест.
    - getSeatsByVehicle (GET): получение списка мест по ID транспортного средства.

    Создание (POST) и удаление (DELETE) отключены, так как:
    - Места создаются автоматически при создании транспортного средства (через сигналы).
    - Удаление мест разрешается только через удаление транспортного средства.


    """

    queryset = Seat.objects.all()
    serializer_class = SeatSerializer

    # Получаем пермишеки 😘
    def get_permissions(self):
        return [HasSeatPermission()]

    @swagger_auto_schema(
        operation_description="Получение списка всех мест",
        operation_summary="Список всех мест",
        tags=["Места"]
    )
    def list(self, request, *args, **kwargs):
        try: 
            seats = seat_service.get_all_seats()
            serializer = self.get_serializer(seats, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @swagger_auto_schema(
        operation_description="Получение информации о конкретном месте",
        operation_summary="Детали места",
        tags=["Места"]
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            seat = seat_service.get_seat_by_id(kwargs.get('pk'))
            serializer = self.get_serializer(seat)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

    @swagger_auto_schema(
        operation_description="Частичное обновление информации о месте (только разрешенные поля)",
        operation_summary="Частичное обновление места",
        tags=["Места"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'seat_class': openapi.Schema(type=openapi.TYPE_STRING, description='Тип места (front, middle, back)')
            }
        )
    )
    def partial_update(self, request, *args, **kwargs):
        return self._update(request, partial=True)

    def _update(self, request, partial: bool):
        try:
            seat = seat_service.get_seat_by_id(self.kwargs.get('pk'))
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(seat, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_seat = seat_service.update_seat(seat.id, serializer.validated_data)
            output_serializer = self.get_serializer(updated_seat)
            return Response(output_serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
    @action(detail=False, methods=['get'], url_path=r'by_vehicle/(?P<vehicle_id>\d+)')
    def get_seats_by_vehicle(self, request, vehicle_id=None):
        """Получение списка мест для конкретного транспортного средства"""
        try:
            seats = seat_service.get_seats_by_vehicle(vehicle_id)
            serializer = self.get_serializer(seats, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
