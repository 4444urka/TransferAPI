from django.db import models
from django.utils import timezone
from apps.vehicle.models import Vehicle
from django.core.exceptions import ValidationError
from django.db.models import Q


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

    def __str__(self):
        return f"{self.departure_time.strftime('%Y-%m-%d %H:%M')}: {self.origin} - {self.destination}"
    
    def clean(self):
        """Универсальная валидация для всех способов сохранения"""
        # Проверка времени отправления
        if self.departure_time < timezone.now():
            raise ValidationError({
                'departure_time': 'Нельзя создавать поездки с прошедшей датой отправления'
            })

        # Проверка времени прибытия
        if self.arrival_time <= self.departure_time:
            raise ValidationError({
                'arrival_time': 'Время прибытия должно быть позже отправления'
            })

        # Проверка пересечения временных интервалов
        conflicts = Trip.objects.filter(
            Q(vehicle=self.vehicle),
            Q(departure_time__lt=self.arrival_time),
            Q(arrival_time__gt=self.departure_time)
        ).exclude(pk=self.pk if self.pk else None)

        if conflicts.exists():
            raise ValidationError({
                'vehicle': f'Транспорт занят с {conflicts[0].departure_time} до {conflicts[0].arrival_time}'
            })

        # Проверка цены
        if self.default_ticket_price < 0:
            raise ValidationError({
                'default_ticket_price': 'Цена не может быть отрицательной'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    