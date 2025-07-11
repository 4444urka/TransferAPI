from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError

from apps.auth.models import User
from apps.payment.models import Payment
from apps.seat.models import TripSeat
from apps.trip.models import Trip
from utils.address import find_address_by_name


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
            
            if seat.price_zone == "front":
                price += self.trip.front_seat_price 
            elif seat.price_zone == "middle":
                price += self.trip.middle_seat_price
            elif seat.price_zone == "back":
                price += self.trip.back_seat_price
        return price

    def __str__(self):
        if not self.pk:
            return f"New booking - {self.trip}" if self.trip else "New booking"
        return f"{self.booking_datetime} - {self.user} - {self.trip} - {self.total_price}"

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-booking_datetime']  # Только сортировка по дате бронирования без фильтрации

    def clean(self):
        """Валидация модели бронирования"""

        # Проверяем наличие пользователя
        if not self.user:
            raise ValidationError("Пользователь обязателен")

        if not self.trip:
            return  # Пропускаем проверки, если рейс не указан
        
        if self.trip and not self.trip.is_bookable:
            raise ValidationError("Бронирование недоступно для этой поездки")

        # Проверка pickup_location только если оно указано
        if self.pickup_location and self.pickup_location.strip():
            # Проверяем, соответствует ли адрес уже нашему формату
            try:
                refactored_pickup_location = find_address_by_name(self.pickup_location, self.trip.from_city.name)
                if refactored_pickup_location:
                    self.pickup_location = refactored_pickup_location
                else:
                    raise ValidationError(
                        f"Не найдена локация '{self.pickup_location}' в городе {self.trip.from_city.name}")
            except Exception as e:
                raise ValidationError(f"Ошибка проверки локации получения: {str(e)}")

        # То же самое для dropoff_location
        if self.dropoff_location and self.dropoff_location.strip():
            # Проверяем, соответствует ли адрес уже нашему формату
            try:
                refactored_dropoff_location = find_address_by_name(self.dropoff_location, self.trip.to_city.name)
                if refactored_dropoff_location:
                    self.dropoff_location = refactored_dropoff_location
                else:
                    raise ValidationError(
                        f"Не найдена локация '{self.dropoff_location}' в городе {self.trip.to_city.name}")
            except Exception as e:
                raise ValidationError(f"Ошибка проверки локации высадки: {str(e)}")

        # Вместо пропуска валидации для новых экземпляров, проводим проверку напрямую
        if hasattr(self, '_seats_to_validate'):
            seats_to_validate = self._seats_to_validate
            for seat in seats_to_validate:
                # Проверяем принадлежит ли место транспортному средству рейса
                if seat.vehicle != self.trip.vehicle:
                    raise ValidationError(f"Место {seat} не соответствует транспортному средству рейса")

                # Проверяем, не занято ли место
                if seat.is_booked:
                    raise ValidationError(f"Место {seat} уже забронировано")
            return

        # Для существующих экземпляров
        if self.pk:  # для существующих экземпляров
            for trip_seat in self.trip_seats.all():
                # Проверка принадлежности места транспортному средству рейса
                if trip_seat.seat.vehicle != self.trip.vehicle:
                    raise ValidationError(f"Место {trip_seat.seat} не соответствует транспортному средству рейса")

                # Проверка, не занято ли место в другом бронировании
                if trip_seat.is_booked:
                    current_booking_seats = Booking.objects.get(pk=self.pk).trip_seats.all()
                    if trip_seat not in current_booking_seats:
                        raise ValidationError(f"Место {trip_seat.seat} уже забронировано")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)