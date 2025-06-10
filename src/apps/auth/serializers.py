import logging

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Feedback
from .services import UserService

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'date_joined', 'chat_id'
            ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления данных пользователя.
    Использует методы валидации из UserService для проверки phone_number и chat_id.
    """
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'date_joined', 'chat_id']

    allowed_fields = {'first_name', 'last_name', 'chat_id'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    def validate(self, data):
        extra_fields = set(self.initial_data.keys()) - self.allowed_fields
        if extra_fields:
            raise serializers.ValidationError({
                f"Unexpected fields: {', '.join(extra_fields)}. ",
                f"Allowed fields: {', '.join(self.allowed_fields)}"}
            )
        
        user_id = self.instance.id if self.instance else None

        if 'phone_number' in data:
            data['phone_number'] = self.user_service.validate_phone_number(
                data['phone_number'], user_id=user_id
            )

        if 'chat_id' in data:
            data['chat_id'] = self.user_service.validate_chat_id(
                data['chat_id'], user_id=user_id
            )

        return data

    def update(self, instance, validated_data):
        updated_user = self.user_service.update_user(instance.id, validated_data)
        return updated_user  


class UserRegistrationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    def validate(self, data):
        phone_number = data['phone_number']
        password = data['password']
        
        try:
            self.user_service.validate_user_data(phone_number, password)
        except serializers.ValidationError as e:
            raise e
            
        return data
    
    def create(self, validated_data):
        try:
            # Создание пользователя через сервис
            user = self.user_service.create_user(
                phone_number=validated_data['phone_number'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', '')
            )
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        logger.debug('Creating new token')
        try:
            token = super().get_token(user)

            # Поля, которые будут в токене
            token['phone_number'] = str(user.phone_number)
        except Exception as e:
            logger.error(f'Error creating token: {e}')
            raise serializers.ValidationError('Error creating token')
        logger.info(f'Created new token')
        return token


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'chat_id', 'message', 'message_datetime']
        read_only_fields = ['id', 'message_datetime']