from django.urls import path
from .views import (
    RegistrationUserView,
    MyTokenObtainPairView, 
    MyTokenRefreshView, 
    UserListView, 
    DetailUserView, 
    UpdateUserView,
    CreateFeedbackView
)

urlpatterns = [
    path('register/', RegistrationUserView.as_view(), name='user-register'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/get_user_info/', DetailUserView.as_view(), name='user_detail'),
    path('users/<int:user_id>/update/', UpdateUserView.as_view(), name='user_update'),
    path('feedback/create/', CreateFeedbackView.as_view(), name='feedback_create'),
]