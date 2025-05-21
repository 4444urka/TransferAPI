from django.urls import path
from apps.utils.views import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
] 