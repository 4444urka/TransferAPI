from django.db import models

from apps.vehicle.models import Vehicle

# Выбор типа сиденья
SEAT_TYPES_CHOICES = [
    ("front", "Front"),
    ("middle", "Middle"),
    ("back", "Back"),
]

class Seat(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    seat_number = models.IntegerField()
    seat_type = models.CharField(choices=SEAT_TYPES_CHOICES, max_length=30, default="front")
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.vehicle} - {self.seat_number}"