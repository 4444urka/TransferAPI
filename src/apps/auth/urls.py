from django.urls import path
from .views import RegistrationUserView, MyTokenObtainPairView, MyTokenRefreshView, UserListView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegistrationUserView.as_view(), name='user-register'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path('users/', UserListView.as_view(), name='user_list')
]