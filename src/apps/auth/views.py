from .serializers import UserRegistrationSerializer, MyTokenObtainPairSerializer
from rest_framework import generics
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView


class RegistrationUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer