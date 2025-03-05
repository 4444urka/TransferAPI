from django.db import models

class Trip(models.Model):
    origin = models.CharField(max_length=30)
    destination = models.CharField(max_length=30)
    departure_time = models.TimeField(default='00:00')
    arrival_time = models.TimeField(default='00:00')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.departure_time}: {self.origin} - {self.destination}"
