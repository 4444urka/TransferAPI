from django.contrib.auth.base_user import BaseUserManager

# пока сделано просто чтобы работало, нужно будет смотреть и дорабатывать
class UserManager(BaseUserManager):
    """Кастомный менеджер для создания пользователей."""

    def create_user(self, phone_number, password=None, **extra_fields):
        """Здесь будет прописана основная логика в создании пользователя."""
        if not phone_number:
            raise ValueError('The Phone Number field must be set')

        # Здесь будет валидация номера, что-то вроде:
        # try:
        #     parsed_number = phonenumbers.parse(phone_number, None)
        #     if not phonenumbers.is_valid_number(parsed_number):
        #         raise ValueError('Invalid phone number')
        # except phonenumbers.NumberParseException:
        #     raise ValueError('Invalid phone number format')

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)  # Хеширование пароля
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Создание суперпользователя."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)