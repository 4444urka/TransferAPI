import logging

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from .services import UserService

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'date_joined', 'chat_id'
            ]
    

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
