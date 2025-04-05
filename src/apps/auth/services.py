import logging
from typing import Optional, List, Dict, Any
import phonenumbers
from django.db.models import Q
import django.contrib.auth.password_validation as validators
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import User

class UserService:
    """
    Сервис для работы с моделью User.
    Предоставляет методы для выполнения операций с пользователями.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_user_data(self, phone_number: str, password: str, user=None) -> None:
        """
        Валидация данных пользователя.
        
        Args:
            phone_number: Номер телефона пользователя
            password: Пароль пользователя
            user: Объект пользователя (опционально, для валидации пароля)
            
        Raises:
            ValidationError: Если данные не проходят валидацию
        """
        self.logger.debug('Validating user data')
        
        # Валидация номера телефона (проверка уникальности)
        if User.objects.filter(phone_number=phone_number).exists():
            self.logger.error('User with this phone number already exists')
            raise serializers.ValidationError('User with this phone number already exists')
        
        # Валидация пароля
        if not user:
            user = User(phone_number=phone_number)
            
        try:
            validators.validate_password(password=password, user=user)
        except DjangoValidationError as e:
            self.logger.error(f'Error validating password: {e}')
            raise serializers.ValidationError(str(e))
            
        self.logger.info('User data validation passed')
    
    def get_all_users(self) -> Optional[User]:
        """
        Получить всех пользователей.
        
        Returns:
            Список всех пользователей
            
        Raises:
            Exception: При ошибке доступа к базе данных
        """
        self.logger.debug('Getting all users')
        try:
            users = User.objects.all()
            self.logger.info(f'Got {users.count()} users')
            return users
        except Exception as e:
            self.logger.error(f'Failed to get all users: {e}')
            raise
        
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по id.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            User объект или None, если пользователь не найден
            
        Raises:
            User.DoesNotExist: если пользователь не найден
            Exception: При ошибке доступа к базе данных
        """
        self.logger.debug(f"Trying to get user by id: {user_id}")
        try:
            user = User.objects.get(id=user_id)
            self.logger.info(f"Successfully got user with id {user_id}")
            return user
        except User.DoesNotExist:
            self.logger.error(f"User with id {user_id} not found")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get user by id: {e}")
            raise
            
    def get_user_by_phone_number(self, phone_number: str) -> User:
        """
        Получить пользователя по номеру телефона.
        
        Args:
            phone_number: Номер телефона пользователя
            
        Returns:
            User объект
            
        Raises:
            User.DoesNotExist: Если пользователь не найден
            Exception: При ошибке доступа к базе данных
        """
        self.logger.debug(f"Trying to get user by phone")
        
        try:
            user = User.objects.get(phone_number=phone_number)
            self.logger.info(f"Successfully got user by phone")
            return user
        except User.DoesNotExist:
            self.logger.error(f"User with phone number not found")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get user by phone: {e}")
            raise
    
    def create_user(self, phone_number: str, password: str, first_name: str = None, last_name: str = None) -> User:
        """
        Создать пользователя.
        
        Args:
            phone_number: Номер телефона пользователя
            password: Пароль пользователя
            first_name: Имя пользователя (опционально)
            last_name: Фамилия пользователя (опционально)
            
        Returns:
            Созданный пользователь
            
        Raises:
            ValidationError: Если данные не проходят валидацию
            Exception: При ошибке создания пользователя
        """
        self.logger.debug('Creating new user')
        try:
            # Валидируем данные пользователя
            self.validate_user_data(phone_number, password)
            
            # Создаем пользователя через стандартный менеджер
            user = User.objects.create_user(
                phone_number=phone_number,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
                
            self.logger.info(f'Created new user')
            return user
        except Exception as e:
            self.logger.error(f'Error creating user: {e}')
            raise serializers.ValidationError(f'Error creating user: {str(e)}')
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """
        Обновить данные пользователя.
        
        Args:
            user_id: Идентификатор пользователя
            data: Словарь с данными для обновления
            current_user: объект пользователя, который сделал запрос
            
        Returns:
            Обновленный объект пользователя или None, если пользователь не найден
            
        Raises:
            Exception: При ошибке обновления
        """
        self.logger.debug(f'Updating user with id {user_id}')
        try:
            user = self.get_user_by_id(user_id)

            allowed_fields = ['first_name', 'last_name', 'phone_number', 'chat_id']
            update_fields = []

            mutable_data = data.copy() if hasattr(data, 'copy') else data
            
            for field in allowed_fields:
                if field == 'phone_number' and 'phone_number' in mutable_data:
                    try:
                        parsed_number = phonenumbers.parse(mutable_data[field], None)
                        if not phonenumbers.is_valid_number(parsed_number):
                            self.logger.error('Invalid phone number')
                            raise serializers.ValidationError({'phone_number':'Invalid phone number'})
                        phone_str = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                        mutable_data[field] = phone_str
                    except:
                        self.logger.error('Invalid phone number')
                        raise serializers.ValidationError({'phone_number':'Invalid phone number'})
                    
                    if User.objects.filter(phone_number=mutable_data[field]).exclude(id=user_id).exists():
                        self.logger.error('Phone number already in use')
                        raise serializers.ValidationError({'phone_number': 'Phone number already in use'})
                    
                if field == 'chat_id' and 'chat_id' in mutable_data:
                    chat_id = str(mutable_data[field]) if isinstance(mutable_data[field], int) else mutable_data[field]
                    if not chat_id.isdigit():
                        raise serializers.ValidationError({'chat_id': 'Chat id must be numeric'})
                    if User.objects.filter(chat_id=mutable_data[field]).exclude(id=user_id).exists():
                        self.logger.error('Chat ID already in use')
                        raise serializers.ValidationError({'chat_id': 'Chat ID already registered'})
                    mutable_data[field] = chat_id

                if field in mutable_data:
                    setattr(user, field, mutable_data[field])
                    update_fields.append(field)
            
            if update_fields:
                user.save(update_fields=update_fields)
                self.logger.info(f'Updated user {user_id}: {", ".join(update_fields)}')
            
            return user
        except Exception as e:
            self.logger.error(f'Error updating user {user_id}: {e}')
            raise
    
    def search_users(self, query: str) -> List[User]:
        """
        Поиск пользователей по имени, фамилии или номеру телефона.
        
        Args:
            query: Строка поиска
            
        Returns:
            Список найденных пользователей
            
        Raises:
            Exception: При ошибке поиска
        """
        self.logger.debug(f'Searching users with query: {query}')
        try:
            users = User.objects.filter(
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) | 
                Q(phone_number__icontains=query)
            )
            self.logger.info(f'Found {users.count()} users matching query: {query}')
            return list(users)
        except Exception as e:
            self.logger.error(f'Error searching users: {e}')
            raise
    
    def delete_user(self, user_id: int) -> bool:
        """
        Удалить пользователя по ID.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            True, если пользователь успешно удален, False если пользователь не найден
            
        Raises:
            Exception: При ошибке удаления
        """
        self.logger.debug(f'Deleting user with id: {user_id}')
        try:
            user = self.get_user_by_id(user_id)
            user.delete()
            self.logger.info(f'User with id {user_id} successfully deleted')
            return True
        except Exception as e:
            self.logger.error(f'Error deleting user {user_id}: {e}')
            raise