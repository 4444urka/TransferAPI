from drf_yasg.utils import swagger_auto_schema

from .serializers import UserRegistrationSerializer, MyTokenObtainPairSerializer, UserSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Администратор получает список всех пользователей
            return User.objects.all()
        # Обычный пользователь – только свои данные
        return User.objects.filter(id=user.id)

    @swagger_auto_schema(
        operation_description="Получение списка пользователей. Администратор получает всех, обычный пользователь – только себя.",
        operation_summary="Список пользователей",
        tags=["Пользователи"]
    )
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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