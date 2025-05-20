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
        app_label = 'transfer_trip'

    def __str__(self):
        return self.name


class Trip(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE, 
        default=1,
        verbose_name="Транспорт"
        )
    from_city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='departures',
        verbose_name="Город отправления"
    )
    to_city = models.ForeignKey(
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

    front_seat_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name="Цена переднего места"
    )
    middle_seat_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name="Цена среднего места"
    )
    back_seat_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name="Цена заднего места"
    )

    is_bookable = models.BooleanField(default=True, verbose_name="Доступна для бронирования")
    is_active = models.BooleanField(default=True, verbose_name="Поездка активна")
    booking_cutoff_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="Время до начала поездки за которое нельзя бронировать поездку (в минутах)",
    )

    class Meta:
        verbose_name = "Поездка"
        verbose_name_plural = "Поездки"
        ordering = ['departure_time', 'arrival_time']
        app_label = 'transfer_trip'

    def __str__(self):
        return f"{self.departure_time.strftime('%Y-%m-%d %H:%M')}: {self.from_city} - {self.to_city}"

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

        # Добавляем проверку: город отправления должен отличаться от города прибытия
        if self.from_city == self.to_city:
            raise ValidationError({
                'to_city': 'Город назначения должен отличаться от города отправления'
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

        # Проверка цен
        if self.front_seat_price < 0:
            raise ValidationError({
                'front_seat_price': 'Цена переднего места не может быть отрицательной'
            })
        if self.middle_seat_price < 0:
            raise ValidationError({
                'middle_seat_price': 'Цена среднего места не может быть отрицательной'
            })
        if self.back_seat_price < 0:
            raise ValidationError({
                'back_seat_price': 'Цена заднего места не может быть отрицательной'
            })
        
        # Проверка времени до отправления
        time_until_departure = (self.departure_time - timezone.now()).total_seconds() / 60
        if self.booking_cutoff_minutes > time_until_departure:
            raise ValidationError({
                'booking_cutoff_minutes': 'Время не может быть больше оставшегося времени до отправления'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

