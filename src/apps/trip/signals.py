from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

from apps.trip.models import Trip
from apps.seat.services.trip_seat_service import TripSeatService
from apps.trip.tasks import disable_booking_for_trip, deactivate_trip

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Trip)
def create_trip_seats(sender, instance, created, **kwargs):
    """Создает записи TripSeat для каждого места транспортного средства при создании поездки"""
    trip_seat_service = TripSeatService()
    if created:
        trip_seat_service.create_trip_seats(instance)


@receiver(post_save, sender=Trip)
def schedule_trip_status_updates(sender, instance: Trip, created: bool, **kwargs):
    """
    При создании поездки планируются две задачи:
    1. По истечении (departure_time - booking_cutoff_minutes) устанавливается is_bookable = False.
    2. По наступлении arrival_time устанавливается is_active = False.
    """
    logger.info("Creating schedule...")
    if created:
        # Вычисляем время отключения бронирования
        cutoff_time = instance.departure_time - timedelta(minutes=instance.booking_cutoff_minutes)
        delay_cutoff = (cutoff_time - timezone.now()).total_seconds()
        if delay_cutoff > 0:
            logger.info("Timeout started")
            disable_booking_for_trip.apply_async(args=[instance.id], countdown=delay_cutoff)
        else:
            logger.info("Instance starting")
            disable_booking_for_trip.delay(instance.id)

        # Планирование задачи деактивации поездки по arrival_time
        delay_arrival = (instance.arrival_time - timezone.now()).total_seconds()
        if delay_arrival > 0:
            logger.info("Timeout started")
            deactivate_trip.apply_async(args=[instance.id], countdown=delay_arrival)
        else:
            logger.info("Instance starting")
            deactivate_trip.delay(instance.id)
    else:
        logger.info("Tasks did not created...")