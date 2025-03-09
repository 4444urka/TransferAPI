from django.db import models
from django.utils import timezone
from apps.vehicle.models import Vehicle
from django.core.exceptions import ValidationError
from django.db.models import Q


class City(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название города")

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ['name']

    def __str__(self):
        return self.name


class Trip(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE, 
        default=1,
        verbose_name="Транспорт"
        )
    origin = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='departures',
        verbose_name="Город отправления"
    )
    destination = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='arrivals',
        verbose_name="Город назначения"
    )
    departure_time = models.DateTimeField(
        verbose_name="Дата и время отправления"
        )
    arrival_time = models.DateTimeField(
        verbose_name="Дата и время прибытия"
        )

    default_ticket_price = models.DecimalField(
        max_digits=10, decimal_places=2, 
        default=0, verbose_name="Цена билета"
        )

    class Meta:
        verbose_name = "Поездка"
        verbose_name_plural = "Поездки"
        ordering = ['departure_time', 'arrival_time']

    def __str__(self):
        return f"{self.departure_time.strftime('%Y-%m-%d %H:%M')}: {self.origin} - {self.destination}"
    
    def clean(self):
        """Универсальная валидация для всех способов сохранения"""
        # Проверка времени отправления
        if self.departure_time < timezone.now():
            raise ValidationError({
                'Дата и время отправления': 'Нельзя создавать поездки с прошедшей датой отправления'
            })

        # Проверка времени прибытия
        if self.arrival_time <= self.departure_time:
            raise ValidationError({
                'Дата и время прибытия': 'Время прибытия должно быть позже отправления'
            })

        # Проверка пересечения временных интервалов
        conflicts = Trip.objects.filter(
            Q(vehicle=self.vehicle),
            Q(departure_time__lt=self.arrival_time),
            Q(arrival_time__gt=self.departure_time)
        ).exclude(pk=self.pk if self.pk else None)

        if conflicts.exists():
            raise ValidationError({
                'Транспорт': f'Транспорт занят с {conflicts[0].departure_time} до {conflicts[0].arrival_time}'
            })

        # Проверка цены
        if self.default_ticket_price < 0:
            raise ValidationError({
                'Цена билета': 'Цена не может быть отрицательной'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    