import logging

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User

logger = logging.getLogger(__name__)

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'password']
        extra_kwargs = {
            'phone_number': {'write_only': True},
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        logger.debug('Creating new user')
        try:
            user = User.objects.create_user(
                phone_number=validated_data['phone_number'],
                password=validated_data['password']
            )
        except Exception as e:
            logger.error(f'Error creating user: {e}')
            raise serializers.ValidationError('Error creating user')
        logger.info(f'Created new user: {user}')
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
        logger.info(f'Created new token: {token}')
        return token
