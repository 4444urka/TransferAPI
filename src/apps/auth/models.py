from django.contrib.auth.models import AbstractBaseUser, Group, Permission
from django.db import models
from .managers import UserManager

class User(AbstractBaseUser):
    """Кастомная модель пользователя с аутентификацией по phone_number."""

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        help_text="Enter phone number in international format (e.g., +1234567890)"
    )
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)  # Активен ли пользователь
    is_staff = models.BooleanField(default=False)  # Является ли администратором
    date_joined = models.DateTimeField(auto_now_add=True)
    is_superuser = models.BooleanField(default=False)

    # Добавляем группы и разрешения
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name="customuser_set",
        related_query_name="customuser"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="customuser_set",
        related_query_name="customuser"
    )


    # Указываем, что аутентификация будет происходить по phone_number
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    # Используем наш кастомный менеджер ( мы наследуемся от AbstractBaseUser,
    # а значит надо определять заново необходимые медоты, для этого и нужен UserManager())
    objects = UserManager()


    def __str__(self):
        return self.phone_number

    def has_perm(self, perm, obj=None):
        """Проверка прав доступа (требуется для админ-панели)."""
        return self.is_staff

    def has_module_perms(self, app_label):
        """Проверка прав доступа к модулю (требуется для админ-панели)."""
        return self.is_staff
