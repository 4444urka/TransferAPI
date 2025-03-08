from django.db import models
from django.utils import timezone

from apps.vehicle.models import Vehicle


class Trip(models.Model):
    origin = models.CharField(max_length=30)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, default=1)
    destination = models.CharField(max_length=30)
    departure_time = models.DateTimeField(
        help_text="Дата и время отправления"
        )
    arrival_time = models.DateTimeField(
        help_text="Дата и время прибытия"
        )

    default_ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # время в формате UTC
    def __str__(self):
        return f"{self.departure_time.strftime('%Y-%m-%d %H:%M')}: {self.origin} - {self.destination}"
