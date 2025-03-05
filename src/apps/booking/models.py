from django.db import models

from apps.auth.models import User
from apps.trip.models import Trip


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    trip = models.ForeignKey(Trip, on_delete=models.DO_NOTHING, default=1)
    # TODO: Добавить связзи с другими моделями (и создать их)
    booking_datetime = models.DateTimeField()





