from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from apps.auth.models import User
from apps.payment.models import Payment
from apps.seat.models import Seat
from apps.trip.models import Trip
from apps.vehicle.models import Vehicle
from utils.is_location_exists import is_location_exists


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

    seats = models.ManyToManyField(
        Seat,
        blank=True,
        verbose_name="Место"
        )

    @property
    def total_price(self):
        """Расчёт итоговой стоимости бронирования"""
        # Пропускаем расчет для несохраненных экземпляров
        if not self.pk:
            return Decimal(0)

        price = Decimal(0)
        for seat in self.seats.all():
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
        """Валидация модели бронирования"""

        # Проверяем наличие пользователя
        if not self.user:
            raise ValidationError("Пользователь обязателен")

        if not self.trip:
            return  # Пропускаем проверки, если рейс не указан

        # Проверяем существует ли адрес на котором нужно забрать пассажира
        if not is_location_exists(self.pickup_location, self.trip.origin.name):
            raise ValidationError(f"Локации {self.pickup_location} не существует в городе {self.trip.origin.name}")

        # Проверяем существует ли адрес на котором нужно высадить пассажира
        if not is_location_exists(self.dropoff_location, self.trip.destination.name):
            raise ValidationError(
                f"Локации {self.dropoff_location} не существует в городе {self.trip.destination.name}")

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
        if self.pk:
            for seat in self.seats.all():
                # Проверяем принадлежит ли место транспортному средству рейса
                if seat.vehicle != self.trip.vehicle:
                    raise ValidationError(f"Место {seat} не соответствует транспортному средству рейса")

                # Проверяем, не занято ли место в другом бронировании
                if seat.is_booked:
                    current_booking_seats = Booking.objects.get(pk=self.pk).seats.all()
                    if seat not in current_booking_seats:
                        raise ValidationError(f"Место {seat} уже забронировано")

            # Проверка соответствия суммы платежа общей стоимости
            if self.payment:
                calculated_total = self.total_price
                if self.payment.amount != calculated_total:
                    raise ValidationError(
                        f"Сумма платежа ({self.payment.amount}) не соответствует общей стоимости ({calculated_total})"
                    )

    def save(self, *args, **kwargs):
        # Вызываем валидацию перед сохранением
        self.full_clean()
        # Сохраняем объект
        super().save(*args, **kwargs)


@receiver(m2m_changed, sender=Booking.seats.through)
def update_seat_booking_status(sender, instance, action, pk_set, **kwargs):
    """Обновляет статус бронирования мест при их добавлении или удалении из бронирования"""
    if action == "post_add" and pk_set:
        # Отмечаем места как забронированные после их добавления в бронирование
        seats = Seat.objects.filter(pk__in=pk_set)
        for seat in seats:
            seat.is_booked = True
            seat.save()

    elif action == "post_remove" and pk_set:
        # Освобождаем места при удалении из бронирования
        seats = Seat.objects.filter(pk__in=pk_set)
        for seat in seats:
            # Проверяем используется ли место в любом другом активном бронировании
            if not Booking.objects.filter(seats=seat, is_active=True).exists():
                seat.is_booked = False
                seat.save()