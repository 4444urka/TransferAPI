from .serializers import UserRegistrationSerializer
from rest_framework import generics
from .models import User


class RegistrationUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer