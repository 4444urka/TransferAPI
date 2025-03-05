from django.utils import timezone

from django.db import models

from apps.auth.models import User
from apps.seat.models import Seat
from apps.trip.models import Trip
from apps.vehicle.models import Vehicle


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    trip = models.ForeignKey(Trip, on_delete=models.DO_NOTHING, default=1)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.DO_NOTHING, default=1)
    booking_datetime = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    seats = models.ManyToManyField(Seat, blank=True)

    def __str__(self):
        return f"{self.user} - {self.trip} - {self.booking_datetime}"



