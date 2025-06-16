from rest_framework import permissions


class HasSeatPermission(permissions.BasePermission):
    """
    Пермишены для seat эндпоинтов:
    - Просмотр списка мест доступен всем авторизированным пользователям
    - Редактирование удаление и создание мест доступно только пользователям с соответствующими правами
    """


    def has_permission(self, request, view):
        # Если пользователь не аутентифицирован, доступ запрещен
        if not request.user.is_authenticated:
            return False
        
        # Если суперчелик, то нуууу проходи
        if request.user.is_superuser:
            return True

        # Пусть смотрит
        if view.action in ['list', 'retrieve', 'get_seats_by_vehicle']:
            return True

        # Если пользователь хочет создать место, то он должен иметь право на это
        elif view.action == 'create' and request.user.has_perm('seat.can_create_seat'):
            return True

        # И то же самое для обновления и удаления ☺️
        elif view.action in ['update', 'partial_update'] and request.user.has_perm('seat.can_update_seat'):
            return True


        elif view.action == 'destroy' and request.user.has_perm('seat.can_delete_seat'):
            return True
        
        return False





