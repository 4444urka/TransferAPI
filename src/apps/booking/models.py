from decimal import Decimal

from django.utils import timezone

from django.db import models

from apps.auth.models import User
from apps.payment.models import Payment
from apps.seat.models import Seat
from apps.trip.models import Trip
from apps.vehicle.models import Vehicle


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    trip = models.ForeignKey(Trip, on_delete=models.DO_NOTHING, default=1)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, blank=True, null=True)
    booking_datetime = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    seats = models.ManyToManyField(Seat, blank=True)

    @property
    def total_price(self):
        """Расчёт итоговой стоимости бронирования"""
        price = Decimal(0)
        for seat in self.seats.all():
            # TODO: Пока что за переднее место надбавка 20%
            multiplier = Decimal(1.2) if seat.seat_type == "front" else Decimal(1.0)
            price += round(self.trip.default_ticket_price * multiplier)
        return price

    def __str__(self):
        return f"{self.booking_datetime} - {self.user} - {self.trip} - {self.total_price}"



