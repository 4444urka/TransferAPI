from rest_framework import permissions


class HasVehiclePermission(permissions.BasePermission):
    """
    Пермишены для vehicle эндпоинтов:
    - Просмотр списка транспортных средств доступен всем авторизированным пользователям
    - Редактирование удаление и создание транспортных средств доступно только пользователям с соответствующими правами
    """
    def has_permission(self, request, view):
        # Если пользователь не аутентифицирован, то нах его
        if not request.user.is_authenticated:
            return False

        # Если суперчелик, то нуууу проходи
        if request.user.is_superuser:
            return True

        # Если авторизированный пользователь, то пусть смотрит
        if view.action in ['list', 'retrieve', 'availability']:
            return True

        # Если пользователь хочет создать транспортное средство, то он должен иметь право на это
        elif view.action == 'create' and request.user.has_perm('vehicle.can_create_vehicle'):
            return True

        # И то же самое для обновления и удаления ☺️
        elif view.action in ['update', 'partial_update'] and request.user.has_perm('vehicle.can_update_vehicle'):
            return True

        elif view.action == 'destroy' and request.user.has_perm('vehicle.can_delete_vehicle'):
            return True