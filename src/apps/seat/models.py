from django.db import models
from django.core.exceptions import ValidationError

from apps.vehicle.models import Vehicle

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
    is_booked = models.BooleanField(default=False, verbose_name="Забронировано")

    class Meta:
        unique_together = ('vehicle', 'seat_number')
        ordering = ['vehicle', 'seat_number']
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def clean(self):
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

    def __str__(self):
        return f"{self.vehicle} - Место {self.seat_number} ({self.get_seat_type_display()})"