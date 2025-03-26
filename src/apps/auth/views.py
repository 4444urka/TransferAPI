from drf_yasg.utils import swagger_auto_schema

from .services import UserService
from .permissions import HasUserPermissions
from .serializers import UserRegistrationSerializer, MyTokenObtainPairSerializer, UserSerializer
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class DetailUserView(generics.RetrieveAPIView):
    user_service = UserService()
    serializer_class = UserSerializer
    permission_classes = [HasUserPermissions]

    def get_object(self):
        return self.request.user  # Возвращаем текущего пользователя из запроса

    @swagger_auto_schema(
        operation_description="Получение информации о пользователе",
        operation_summary="Информация о пользователе",
        tags=["Пользователи"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserListView(generics.ListAPIView):
    user_service = UserService()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, HasUserPermissions]

    def get_queryset(self):
        # Проверяем права доступа - администраторы видят всех, обычные пользователи - только себя
        if self.request.user.is_staff or self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @swagger_auto_schema(
        operation_description="Получение списка пользователей. Администраторы получают всех, обычные пользователи - только себя.",
        operation_summary="Список пользователей",
        tags=["Пользователи"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
        


class RegistrationUserView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        operation_summary="Регистрация",
        tags=["Пользователи"]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"id": user.id, "message": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )


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