from django.db import models
from django.core.exceptions import ValidationError

from apps.vehicle.models import Vehicle
from apps.trip.models import Trip

# Выбор типа сиденья
SEAT_TYPES_CHOICES = [
    ("front", "Переднее"),
    ("middle", "Среднее"),
    ("back", "Заднее"),
]


class Seat(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name="Транспорт")
    seat_number = models.IntegerField(verbose_name="Номер места")
    seat_type = models.CharField(
        choices=SEAT_TYPES_CHOICES,
        max_length=30,
        default="front",
        verbose_name="Тип места"
    )

    class Meta:
        unique_together = ('vehicle', 'seat_number')
        ordering = ['vehicle', 'seat_number']
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

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
            raise ValidationError({
                'seat_number': 'Номер места должен быть положительным числом'
            })

        if self.seat_number > self.vehicle.total_seats:
            raise ValidationError({
                'seat_number': f'Номер места не может быть больше общего количества мест ({self.vehicle.total_seats})'
            })
                  
        # Проверка при изменении существующего объекта:

        # Вообще до этой проверки дойти не должно, потому что введен запрет  
        # на удаление мест, но на всякий склучай пусть будет прописано явно
        
        if self.pk:
            original = Seat.objects.get(pk=self.pk)
            if original.seat_number != self.seat_number:
                raise ValidationError({
                    'seat_number': 'Редактирование номера места запрещено'
                })
            if original.vehicle != self.vehicle:
                raise ValidationError({
                    'vehicle': 'Изменение транспортного средства запрещено'
                })

        # # проверка типа места в зависимости от номера
        # if self.seat_number == 1 and self.seat_type != "front":
        #     raise ValidationError({
        #         'seat_type': 'Первое место должно быть переднего типа'
        #     })
        # elif self.seat_number == 1 and self.seat_type == "front":
        #     pass  # первое место переднее - всё ок
        # elif self.seat_type == "front":
        #     raise ValidationError({
        #         'seat_type': 'Только первое место может быть переднего типа'
        #     })        

            
    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

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
            if calling_frame and 'manage_seats' in calling_frame.f_code.co_name:
                # Если вызов идет из функции manage_seats в signals.py, разрешаем удаление
                return super().delete(*args, **kwargs)
        finally:
            del frame  # Освобождаем фрейм во избежание утечек памяти

        # Для всех остальных случаев - запрещаем удаление
        raise ValidationError(
            "Удаление мест запрещено. Удалите транспортное средство или измените количество мест."
        )

    def __str__(self):
        return f"{self.vehicle} - Место {self.seat_number} ({self.get_seat_type_display()})"


class TripSeat(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='trip_seats', verbose_name="Поездка")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='trip_seats', verbose_name="Место")
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Цена места"
    )
    is_booked = models.BooleanField(default=False, verbose_name="Забронировано")

    class Meta:
        unique_together = ('trip', 'seat')
        verbose_name = 'Бронирования мест'
        verbose_name_plural = 'Бронирование места'

    def __str__(self):
        return f"{self.trip} - {self.seat} - {'Забронировано' if self.is_booked else 'Свободно'}"