from rest_framework import permissions


class HasTripPermission(permissions.BasePermission):
    """
    Разрешения для поездок:
    - Просмотр списка поездок и деталей поездки и мест поездки доступен всем пользователям
    - Создание, изменение и удаление поездок доступно пользователям со специальными правами:
      - can_create_trip - право на создание поездок
      - can_update_trip - право на изменение поездок
      - can_delete_trip - право на удаление поездок
    - Администраторы (is_staff=True) имеют полный доступ ко всем операциям
    """

    def has_permission(self, request, view):

        # Администраторы имеют полный доступ
        if request.user.is_superuser:
            return True

        if view.action in ['list', 'retrieve', 'cities', 'seats']:
            return True

        # Для создания, требуется право can_create_trip или статус администратора
        if view.action == 'create' and request.user.has_perm('trip.can_create_trip'):
            return True

        # Для изменения и удаления потребуются дополнительные проверки на уровне объекта
        if view.action in ['update', 'partial_update', 'destroy']:
            return True

        # Для остальных действий запрещаем
        return False

    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_superuser:
            return True

        # Просмотр доступен всем пользователям
        if view.action in ['retrieve', 'seats']:
            return True

        # Обновление требует наличия права can_update_trip
        if view.action in ['update', 'partial_update'] and request.user.has_perm('trip.can_update_trip'):
            return True

        # Удаление требует наличия права can_delete_trip
        if view.action == 'destroy' and request.user.has_perm('trip.can_delete_trip'):
            return True

        # В остальных случаях запрещаем
        return False
    