from django.urls import path
from .views import SystemHealthView, ModuleHealthView

urlpatterns = [
    path('health/', SystemHealthView.as_view(), name='system-health'),
    path('modules/', ModuleHealthView.as_view(), name='module-health'),
] 