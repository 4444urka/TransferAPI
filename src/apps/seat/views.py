# apps/seat/views.py

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
from apps.seat.models import Seat
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
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer

    # Переопределяем методы, чтобы все же получать понятные ответы даже при ручном вызове
    def create(self, request, *args, **kwargs):
        # Запрещаем создание мест через API
        return Response(
            {"detail": "Создание мест через API запрещено"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        # Запрещаем удаление мест через API
        return Response(
            {"detail": "Удаление мест через API запрещено"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
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