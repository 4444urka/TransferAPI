# apps/seat/views.py

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from apps.seat.models import Seat
from apps.seat.serializers import SeatSerializer

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
