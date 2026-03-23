from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.auth.models import User
from apps.vehicle.models import Vehicle


class City(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название города")

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ["name"]
        app_label = "transfer_trip"

    def __str__(self):
        return self.name


class Trip(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, default=1, verbose_name="Транспорт"
    )
    driver = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trips",
        verbose_name="Водитель",
    )
    from_city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="departures",
        verbose_name="Город отправления",
    )
    to_city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="arrivals",
        verbose_name="Город назначения",
    )
    departure_time = models.DateTimeField(verbose_name="Дата и время отправления")
    arrival_time = models.DateTimeField(verbose_name="Дата и время прибытия")

    economy_seat_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Цена места Эконом"
    )
    comfort_seat_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Цена места Комфорт"
    )

    is_bookable = models.BooleanField(
        default=True, verbose_name="Доступна для бронирования"
    )
    is_active = models.BooleanField(default=True, verbose_name="Поездка активна")
    booking_cutoff_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="Время до начала поездки за которое нельзя бронировать поездку (в минутах)",
    )

    class Meta:
        verbose_name = "Поездка"
        verbose_name_plural = "Поездки"
        ordering = ["departure_time", "arrival_time"]
        app_label = "transfer_trip"

    def __str__(self):
        return f"{self.departure_time.strftime('%Y-%m-%d %H:%M')}: {self.from_city} - {self.to_city}"

    def clean(self):
        """Универсальная валидация для всех способов сохранения"""

        if not self.driver.groups.filter(name="Водитель").exists():
            raise ValidationError(
                {"driver": "Выбранный пользователь не является водителем"}
            )

        driver_conflicts = Trip.objects.filter(
            Q(driver=self.driver),
            Q(departure_time__lt=self.arrival_time),
            Q(arrival_time__gt=self.departure_time),
        ).exclude(pk=self.pk if self.pk else None)

        if driver_conflicts.exists():
            raise ValidationError(
                {
                    "driver": f"Водитель занят с {driver_conflicts[0].departure_time} до {driver_conflicts[0].arrival_time}"
                }
            )

        if self.departure_time < timezone.now() and (
            self.is_active == True or self.is_bookable == True
        ):
            raise ValidationError(
                {
                    "departure_time": "Прошедшие поездки не могут быть активными или доступными для бронирования"
                }
            )

        # Проверка времени прибытия
        if self.arrival_time <= self.departure_time:
            raise ValidationError(
                {"arrival_time": "Время прибытия должно быть позже отправления"}
            )

        # Добавляем проверку: город отправления должен отличаться от города прибытия
        if self.from_city == self.to_city:
            raise ValidationError(
                {"to_city": "Город назначения должен отличаться от города отправления"}
            )

        # Проверка пересечения временных интервалов
        conflicts = Trip.objects.filter(
            Q(vehicle=self.vehicle),
            Q(departure_time__lt=self.arrival_time),
            Q(arrival_time__gt=self.departure_time),
        ).exclude(pk=self.pk if self.pk else None)

        if conflicts.exists():
            raise ValidationError(
                {
                    "vehicle": f"Транспорт занят с {conflicts[0].departure_time} до {conflicts[0].arrival_time}"
                }
            )

        # Проверка цен
        if self.economy_seat_price < 0:
            raise ValidationError(
                {"economy_seat_price": "Цена места Эконом не может быть отрицательной"}
            )
        if self.comfort_seat_price < 0:
            raise ValidationError(
                {"comfort_seat_price": "Цена места Комфорт не может быть отрицательной"}
            )

        # Проверка времени до отправления
        time_until_departure = (
            self.departure_time - timezone.now()
        ).total_seconds() / 60

        # Проверка на то, что время до отправления не может быть меньше времени до отправления и время прибытия не может быть в прошлом
        if (
            self.booking_cutoff_minutes > time_until_departure
            and self.arrival_time > timezone.now()
        ):
            raise ValidationError(
                {
                    "booking_cutoff_minutes": "Время не может быть больше оставшегося времени до отправления"
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
