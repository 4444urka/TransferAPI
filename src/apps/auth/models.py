from django.contrib.auth.models import AbstractBaseUser, Group, Permission
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager

class User(AbstractBaseUser):
    """Кастомная модель пользователя с аутентификацией по phone_number."""

    phone_number = PhoneNumberField(unique=True,
                                    verbose_name="Номер телефона",
                                    help_text="Введите номер телефона в международном формате (к примеру: +1234567890)")
    first_name = models.CharField(max_length=30, verbose_name="Имя", blank=True, null=True)
    last_name = models.CharField(max_length=30, verbose_name="Фамилия", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")  # Активен ли пользователь
    is_staff = models.BooleanField(default=False, verbose_name="Является администратором")  # Является ли администратором
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время регистрации")
    is_superuser = models.BooleanField(default=False, verbose_name="Является 'суперпользователем'")

    # Добавляем группы и разрешения
    groups = models.ManyToManyField(
        Group,
        verbose_name='Группы',
        blank=True,
        related_name="customuser_set",
        related_query_name="customuser"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='Разрешения пользователя',
        blank=True,
        related_name="customuser_set",
        related_query_name="customuser"
    )


    # Указываем, что аутентификация будет происходить по phone_number
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    # Используем наш кастомный менеджер
    objects = UserManager()


    def __str__(self):
        return f"{self.phone_number} {self.first_name} {self.last_name}"

    def has_perm(self, perm, obj=None):
        """Проверка прав доступа с учетом групп и разрешений"""
        # Суперпользователи имеют все права
        if self.is_superuser:
            return True

        # Проверяем конкретное разрешение
        return self.user_permissions.filter(codename=perm.split('.')[1]).exists() or \
            self.groups.filter(permissions__codename=perm.split('.')[1]).exists()

    def has_module_perms(self, app_label):
        """Проверка прав доступа к модулю с учетом групп и разрешений"""
        # Суперпользователи имеют все права
        if self.is_superuser:
            return True

        # Проверяем разрешения для указанного приложения
        return self.user_permissions.filter(content_type__app_label=app_label).exists() or \
            self.groups.filter(permissions__content_type__app_label=app_label).exists()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['phone_number']
