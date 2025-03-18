from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.cache import cache

from apps.booking.models import Booking
from apps.seat.models import Seat, TripSeat
from apps.trip.models import Trip
from apps.vehicle.models import Vehicle


