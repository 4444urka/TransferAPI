from django.db import models

from apps.vehicle.models import Vehicle

# Выбор типа сиденья
SEAT_TYPES_CHOICES = [
    ("спереди", "Спереди"),
    ("посередине", "Посередине"),
    ("сзади", "Сзади"),
]

class Seat(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        verbose_name="Транспортное средство"
        )
    seat_number = models.IntegerField(verbose_name="Номер места")
    seat_type = models.CharField(
        choices=SEAT_TYPES_CHOICES,
        max_length=30,
        default="спереди",
        verbose_name="расположение места в трансфере"
        )
    is_booked = models.BooleanField(default=False, verbose_name="Место забранированно")

    class Meta:
        verbose_name = "Место в трансфере"
        verbose_name_plural = "Места в трансфере"
        ordering = ['vehicle']

    def __str__(self):
        return f"{self.vehicle} - {self.seat_number}"