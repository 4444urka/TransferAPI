from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.trip.models import Trip
from apps.seat.services.trip_seat_service import TripSeatService


@receiver(post_save, sender=Trip)
def create_trip_seats(sender, instance, created, **kwargs):
    """Создает записи TripSeat для каждого места транспортного средства при создании поездки"""
    trip_seat_service = TripSeatService()
    if created:
        trip_seat_service.create_trip_seats(instance)