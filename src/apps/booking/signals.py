from django.db.models.signals import m2m_changed, pre_delete, pre_save
from django.dispatch import receiver

from apps.booking.models import Booking
from apps.seat.models import TripSeat


@receiver(m2m_changed, sender=Booking.trip_seats.through)
def update_seat_booking_status(sender, instance, action, pk_set, **kwargs):
    """Обновляет статус бронирования мест при их добавлении или удалении из бронирования"""
    if action in ["post_add", "post_remove", "post_clear"]:
        # При добавлении мест обновляем их статус в соответствии с is_active бронирования
        if action == "post_add" and pk_set:
            trip_seats = TripSeat.objects.filter(pk__in=pk_set)
            for trip_seat in trip_seats:
                # Устанавливаем статус забронирован только если бронирование активно
                trip_seat.is_booked = instance.is_active
                trip_seat.save()

        # При очистке всех мест освобождаем их
        elif action in ["post_remove", "post_clear"]:
            #  нам нужно освободить конкретные места, если это post_remove
                trip_seats = TripSeat.objects.filter(pk__in=pk_set)
                for trip_seat in trip_seats:
                    trip_seat.is_booked = False
                    trip_seat.save()


@receiver(pre_delete, sender=Booking)
def release_seats_on_booking_delete(sender, instance, **kwargs):
    """
    Освобождает места при удалении бронирования
    """
    # Освобождаем все места, связанные с этим бронированием
    for trip_seat in instance.trip_seats.all():
        trip_seat.is_booked = False
        trip_seat.save()

@receiver(pre_save, sender=Booking)
def release_seats_on_deactivation(sender, instance, **kwargs):
    # Проверяем, что это существующий объект бронирования
    if instance.pk:
        # Получаем предыдущее состояние объекта
        try:
            previous = Booking.objects.get(pk=instance.pk)
            # Если бронирование становится неактивным
            if previous.is_active and not instance.is_active:
                # Освобождаем места
                for seat in instance.seats.all():
                    seat.is_booked = False
                    seat.save()
        except Booking.DoesNotExist:
            pass