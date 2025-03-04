from django.db import models

from apps.auth.models import User


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    # TODO: Добавить связзи с другими моделями (и создать их)
    booking_datetime = models.DateTimeField()





