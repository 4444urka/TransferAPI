from django.core.exceptions import ValidationError
from django.db import models

from apps.trip.models import Trip
from apps.vehicle.models import Vehicle

# Выбор типа сиденья
SEAT_CLASS_CHOICES = [
    ("economy", "Эконом"),
    ("comfort", "Комфорт"),
]


class Seat(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, verbose_name="Транспорт"
    )
    seat_number = models.IntegerField(verbose_name="Номер места")
    seat_class = models.CharField(
        choices=SEAT_CLASS_CHOICES,
        max_length=30,
        default="economy",
        verbose_name="Класс места",
    )

    class Meta:
        unique_together = ("vehicle", "seat_number")
        ordering = ["vehicle", "seat_number"]
        verbose_name = "Место"
        verbose_name_plural = "Места"

    @property
    def row_index(self):
        """Возвращает номер ряда (начиная с 1)"""
        if self.vehicle.seats_per_row:
            return ((self.seat_number - 1) // self.vehicle.seats_per_row) + 1
        return None

    @property
    def col_index(self):
        """Возвращает номер места в ряду (начиная с 1)"""
        if self.vehicle.seats_per_row:
            return ((self.seat_number - 1) % self.vehicle.seats_per_row) + 1
        return None

    # Метод для проверки доступности места на конкретной поездке
    def is_booked_for_trip(self, trip):
        try:
            trip_seat = TripSeat.objects.get(trip=trip, seat=self)
            return trip_seat.is_booked
        except TripSeat.DoesNotExist:
            return False

    def clean(self):
        super().clean()
        if not self.vehicle_id:
            raise ValidationError("Необходимо указать транспортное средство")

        if not self.seat_number:
            raise ValidationError("Необходимо указать номер места")

        if self.seat_number < 1:
            raise ValidationError(
                {"seat_number": "Номер места должен быть положительным числом"}
            )

        if self.seat_number > self.vehicle.total_seats:
            raise ValidationError(
                {
                    "seat_number": f"Номер места не может быть больше общего количества мест ({self.vehicle.total_seats})"
                }
            )

        # Проверка при изменении существующего объекта:

        # Вообще до этой проверки дойти не должно, потому что введен запрет
        # на удаление мест, но на всякий склучай пусть будет прописано явно

        if self.pk:
            original = Seat.objects.get(pk=self.pk)
            if original.seat_number != self.seat_number:
                raise ValidationError(
                    {"seat_number": "Редактирование номера места запрещено"}
                )
            if original.vehicle != self.vehicle:
                raise ValidationError(
                    {"vehicle": "Изменение транспортного средства запрещено"}
                )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_seat_class = None
        if not is_new:
            try:
                old_seat_class = Seat.objects.get(pk=self.pk).seat_class
            except Seat.DoesNotExist:
                pass

        self.full_clean()
        super().save(*args, **kwargs)

        if not is_new and old_seat_class != self.seat_class:
            for trip_seat in self.trip_seats.select_related("trip").all():
                trip_seat.seat_class = self.seat_class
                if self.seat_class == "comfort":
                    trip_seat.cost = trip_seat.trip.comfort_seat_price
                elif self.seat_class == "economy":
                    trip_seat.cost = trip_seat.trip.economy_seat_price
                trip_seat.save(update_fields=["seat_class", "cost"])

    def delete(self, *args, **kwargs):
        """
        Запрещает удаление отдельных мест через прямой вызов delete().
        Удаление возможно только через удаление транспортного средства
        или через обновление количества мест в транспортном средстве.
        """
        # Проверяем, вызывается ли delete из сигнала обработки обновления vehicle
        import inspect

        frame = inspect.currentframe()
        try:
            calling_frame = frame.f_back
            if calling_frame and "manage_seats" in calling_frame.f_code.co_name:
                # Если вызов идет из функции manage_seats в signals.py, разрешаем удаление
                return super().delete(*args, **kwargs)
        finally:
            del frame  # Освобождаем фрейм во избежание утечек памяти

        # Для всех остальных случаев - запрещаем удаление
        raise ValidationError(
            "Удаление мест запрещено. Удалите транспортное средство или измените количество мест."
        )

    def __str__(self):
        return f"{self.vehicle} - Место {self.seat_number} ({self.get_seat_class_display()})"


class TripSeat(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="trip_seats",
        verbose_name="Поездка",
    )
    seat = models.ForeignKey(
        Seat, on_delete=models.CASCADE, related_name="trip_seats", verbose_name="Место"
    )
    seat_class = models.CharField(
        choices=SEAT_CLASS_CHOICES,
        max_length=30,
        default="economy",
        verbose_name="Класс места",
    )
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Цена места"
    )
    is_booked = models.BooleanField(default=False, verbose_name="Забронировано")

    class Meta:
        unique_together = ("trip", "seat")
        verbose_name = "Бронирования мест"
        verbose_name_plural = "Бронирование места"

    def __str__(self):
        return f"{self.trip} - {self.seat} - {'Забронировано' if self.is_booked else 'Свободно'}"
