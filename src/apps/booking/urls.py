from django.urls import path
from .views import get_trip_seats 

urlpatterns = [
    path('ajax/get_trip_seats/', get_trip_seats, name='ajax_get_trip_seats'),
] 