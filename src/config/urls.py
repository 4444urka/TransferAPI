from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from apps.booking.views import BookingViewSet
from apps.seat.views import SeatViewSet
from config.openapi import schema_view

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'seats', SeatViewSet, basename='seat')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.auth.urls')),
    path('api/trips/', include('apps.trip.urls')),
    path('api/vehicles/', include('apps.vehicle.urls')),
    path('api/', include(router.urls)),
    path('api/monitoring/', include('apps.monitoring.urls')),
    path('', include('apps.booking.urls')),

    # URL для Swagger UI
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]