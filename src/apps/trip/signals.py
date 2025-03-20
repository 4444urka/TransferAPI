from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.seat.models import Seat, TripSeat
from apps.trip.models import Trip


@receiver(post_save, sender=Trip)
def create_trip_seats(sender, instance, created, **kwargs):
    """Создает записи TripSeat для каждого места транспортного средства при создании поездки"""
    if created:
        vehicle_seats = Seat.objects.filter(vehicle=instance.vehicle)
        for seat in vehicle_seats:
            TripSeat.objects.create(trip=instance, seat=seat)