from celery import shared_task
from django.utils import timezone
from apps.trip.models import Trip
from apps.booking.models import Booking 
import logging

logger = logging.getLogger(__name__)


@shared_task()
def disable_booking_for_trip(trip_id: int) -> None:
    """
    Задача, которая отключает возможность бронирования поездки, устанавливая is_bookable = False.
    """
    try:
        Trip.objects.filter(id=trip_id).update(is_bookable=False)
        logger.info(f"Disabled bookable status for trip {trip_id}.")
    except Exception as e:
        logger.error(f"Error with changing bookable status: {e}")

@shared_task()
def deactivate_trip(trip_id: int) -> None:
    """
    Задача, которая помечает поездку как неактивную (is_active = False) по наступлении arrival_time.
    """
    try:
        # Обновляем статус поездки
        trip = Trip.objects.get(id=trip_id)
        trip.is_active = False
        trip.save()
        
        # Обновляем связанные бронирования
        updated_status_booking = Booking.objects.filter(trip=trip).update(is_active=False)
        
        logger.info(f"Deactivated trip {trip_id} and {updated_status_booking} related bookings.")
    except Exception as e:
        logger.error(f"Error with changing active status: {e}")
