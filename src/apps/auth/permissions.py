from rest_framework import permissions


class HasUserPermissions(permissions.BasePermission):
    """
    Разрешения для пользователей:
    - Не аутентифицированные пользователи не имеют доступа
    - Обычные пользователи могут видеть только собственную информацию
    - Администраторы могут видеть информацию о всех пользователях
    """

    def has_permission(self, request, view):
        # Базовая проверка: пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False

        # Администраторы имеют полный доступ
        if request.user.is_superuser:
            return True

        # Для UserListView (который наследуется от ListAPIView)
        if view.__class__.__name__ == 'UserListView' and request.user.has_perm('auth.add_user'):
            # Для обычных пользователей фильтрация будет в get_queryset
            return True

        # Для DetailUserView (который наследуется от RetrieveAPIView)
        if view.__class__.__name__ == 'DetailUserView':
            # Обычные пользователи видят только себя
            return True
        
        if view.__class__.__name__ == 'UpdateUserView':
            return True
        
        if view.__class__.__name__ == 'DeleteUserView':
            return True

        # В остальных случаях запрещаем
        return False

    def has_object_permission(self, request, view, obj):
        # Администраторы имеют полный доступ
        if request.user.is_superuser:
            return True

        # Обычные пользователи видят только себя
        return obj == request.user