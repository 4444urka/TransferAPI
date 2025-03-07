from django.db import models

class Vehicle(models.Model):
    vehicle_type = models.CharField(max_length=30)
    license_plate = models.CharField(max_length=30)
    total_seats = models.IntegerField()

    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate}'
