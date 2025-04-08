from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError

from apps.auth.models import User
from apps.payment.models import Payment
from apps.seat.models import TripSeat
from apps.trip.models import Trip
from utils.address import find_street_by_name


class Booking(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
        )
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        default=1,
        verbose_name="Поездка"
        )
    pickup_location = models.CharField(
        max_length=100,
        verbose_name="Место посадки",
        help_text="Введите улицу и номер дома в формате 'ул. Название, 1'",
        default="",
        )
    dropoff_location = models.CharField(
        max_length=100,
        verbose_name="Место высадки",
        help_text="Введите улицу и номер дома в формате 'ул. Название, 1'",
        default=""
        )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Данные об оплате"
        )
    booking_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время бронирования"
        )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Бронирование актуально"
        )

    trip_seats = models.ManyToManyField(
        TripSeat,
        blank=True,
        verbose_name="Места в поездке",
    )

    @property
    def total_price(self):
        """Расчёт итоговой стоимости бронирования"""
        # Пропускаем расчет для несохраненных экземпляров
        if not self.pk:
            return Decimal(0)

        price = Decimal(0)
        # Получаем все TripSeat для этого бронирования
        for trip_seat in self.trip_seats.all():
            # Получаем объект Seat через связь в TripSeat
            seat = trip_seat.seat
            # TODO: Пока что за переднее место надбавка 20%
            multiplier = Decimal(1.2) if seat.seat_type == "front" else Decimal(1.0)
            price += round(self.trip.default_ticket_price * multiplier)
        return price

    def __str__(self):
        if not self.pk:
            return f"New booking - {self.trip}" if self.trip else "New booking"
        return f"{self.booking_datetime} - {self.user} - {self.trip} - {self.total_price}"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['booking_datetime', 'is_active']

    def clean(self):
        super().clean()
        # Проверяем и изменяем pickup_location
        if self.pickup_location and self.trip and self.trip.origin:
            try:
                refactored = find_street_by_name(self.pickup_location, self.trip.origin.name)
                if refactored:
                    self.pickup_location = refactored
                else:
                    raise ValidationError({
                        'pickup_location': f"Адрес {self.pickup_location} не найден в {self.trip.origin.name}"
                    })
            except Exception as e:
                raise ValidationError({
                    'pickup_location': f"Ошибка обработки адреса {self.pickup_location}: {str(e)}"
                })

        # То же для dropoff_location
        if self.dropoff_location and self.trip and self.trip.destination:
            try:
                refactored = find_street_by_name(self.dropoff_location, self.trip.destination.name)
                if refactored:
                    self.dropoff_location = refactored
                else:
                    raise ValidationError({
                        'dropoff_location': f"Адрес {self.dropoff_location} не найден в {self.trip.destination.name}"
                    })
            except Exception as e:
                raise ValidationError({
                    'dropoff_location': f"Ошибка обработки адреса {self.dropoff_location}: {str(e)}"
                })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)