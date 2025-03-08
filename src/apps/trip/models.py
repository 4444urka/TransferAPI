from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

from apps.vehicle.models import Vehicle


class Trip(models.Model):
    origin = models.CharField(max_length=30)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, default=1)
    destination = models.CharField(max_length=30)
    date = models.DateField(default=timezone.now)
    departure_time = models.TimeField(default='00:00')
    arrival_time = models.TimeField(default='00:00')

    default_ticket_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} {self.departure_time}: {self.origin} - {self.destination}"

    def clean(self):
        super().clean()
        
        # Проверка что время отправления раньше времени прибытия
        if self.departure_time >= self.arrival_time:
            raise ValidationError("Время отправления должно быть раньше времени прибытия")

        # Проверка пересечения с другими поездками того же транспорта
        overlapping_trips = Trip.objects.filter(
            vehicle=self.vehicle,
            date=self.date
        ).exclude(pk=self.pk)

        for trip in overlapping_trips:
            # Проверяем пересечение времени
            if (self.departure_time <= trip.arrival_time and 
                self.arrival_time >= trip.departure_time):
                raise ValidationError(
                    f"Обнаружено пересечение с поездкой {trip}. " +
                    "Транспортное средство уже занято в это время."
                )
            
            # # Проверка минимального интервала между поездками (30 минут) (если понадобится)
            # min_interval = timedelta(minutes=30)
            
            # # Конвертируем время в datetime для сравнения
            # trip_arrival_dt = datetime.combine(self.date, trip.arrival_time)
            # next_departure_dt = datetime.combine(self.date, self.departure_time)
            
            # if abs(next_departure_dt - trip_arrival_dt) < min_interval:
            #     raise ValidationError(
            #         "Минимальный интервал между поездками должен быть 30 минут"
            #     )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
