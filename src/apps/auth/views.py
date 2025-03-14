from drf_yasg.utils import swagger_auto_schema

from .serializers import UserRegistrationSerializer, MyTokenObtainPairSerializer
from rest_framework import generics
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class RegistrationUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        operation_summary="Регистрация",
        tags=["Пользователи"]
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="Получение токена для авторизации",
        operation_summary="Получение токена",
        tags=["Пользователи"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class MyTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_description="Обновление токена для авторизации",
        operation_summary="Обновление токена",
        tags=["Пользователи"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)