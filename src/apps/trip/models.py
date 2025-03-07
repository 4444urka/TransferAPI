from django.db import models
from django.utils import timezone

from apps.vehicle.models import Vehicle


class Trip(models.Model):
    origin = models.CharField(max_length=30)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.DO_NOTHING, default=1)
    destination = models.CharField(max_length=30)
    date = models.DateField(default=timezone.now)
    departure_time = models.TimeField(default='00:00')
    arrival_time = models.TimeField(default='00:00')

    default_ticket_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} {self.departure_time}: {self.origin} - {self.destination}"
