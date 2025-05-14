from drf_yasg.utils import swagger_auto_schema

from .services import UserService
from .permissions import HasUserPermissions
from .serializers import UserRegistrationSerializer, MyTokenObtainPairSerializer, UserSerializer, UserUpdateSerializer
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

user_service = UserService()

class DetailUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [HasUserPermissions]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_description="Получение информации о пользователе",
        operation_summary="Информация о пользователе",
        tags=["Пользователи"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, HasUserPermissions]

    def get_queryset(self):
        return list(user_service.get_all_users())

    @swagger_auto_schema(
        operation_description="Получение списка пользователей. Администраторы получают всех, обычные пользователи - только себя.",
        operation_summary="Список пользователей",
        tags=["Пользователи"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    
class UpdateUserView(generics.GenericAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated, HasUserPermissions]
    lookup_field = 'id'
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        return user_service.get_all_users()

    @swagger_auto_schema(
        operation_description="Обновление данных пользователя",
        operation_summary="Обновление пользователя",
        tags=["Пользователи"],
    )
    def patch(self, request, *args, **kwargs):
        user_to_update = self.get_object()
        serializer = self.get_serializer(instance=user_to_update, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save() # вызов update_user инкапсулирован в сериализаторе
        return Response(self.get_serializer(updated_user).data, status=status.HTTP_200_OK)


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