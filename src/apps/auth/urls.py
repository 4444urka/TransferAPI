from django.urls import path
from .views import RegistrationUserView

urlpatterns = [
    path('register/', RegistrationUserView.as_view(), name='user-register')
]