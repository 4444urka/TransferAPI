from django.db import models

class Trip(models.Model):
    origin = models.CharField(max_length=30)
    destination = models.CharField(max_length=30)
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.origin} - {self.destination}"
