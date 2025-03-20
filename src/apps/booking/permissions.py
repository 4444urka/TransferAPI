from rest_framework import permissions


class HasBookingPermission(permissions.BasePermission):
    """
    Разрешения для бронирований:
    - Обычные пользователи видят только свои бронирования
    - Пользователи с правом 'can_view_all_booking' видят все бронирования
    - Для создания бронирования требуется только аутентификация
    - Для изменения и удаления требуются соответствующие права или владение объектом
    """

    def has_permission(self, request, view):
        # Для всех действий требуется аутентификация
        if not request.user.is_authenticated:
            return False

        # Для действия list не нужны дополнительные проверки
        if view.action == 'list':
            return True

        # Для создания бронирования достаточно быть аутентифицированным
        if view.action == 'create':
            return True

        # Для остальных действий проверка объекта будет в has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_staff:
            return True

        # Владельцы могут просматривать, изменять и удалять свои бронирования
        if obj.user == request.user:
            return True

        # Пользователи со специальным разрешением могут просматривать все
        if view.action == 'retrieve' and request.user.has_perm('booking.can_view_all_booking'):
            return True

        # В остальных случаях запрещаем
        return False