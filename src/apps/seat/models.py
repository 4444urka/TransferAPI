from django.db import models

from apps.vehicle.models import Vehicle


class Seat(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.DO_NOTHING)
    seat_number = models.IntegerField()
    seat_class = models.CharField(max_length=30)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vehicle} - {self.seat_number}"