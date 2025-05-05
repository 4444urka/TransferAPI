from django.db.models.signals import m2m_changed, pre_delete, pre_save, post_save, post_delete
from django.dispatch import receiver
import logging
from django.conf import settings
from apps.booking.models import Booking
from apps.seat.models import TripSeat
import requests
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache


logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=Booking.trip_seats.through)
def update_trip_seat_status(sender, instance, action, pk_set, **kwargs):
    """
    Обновляет статус is_booked у TripSeat при изменении M2M связи с Booking.
    """
    
    if action == "post_add":
        # Места были добавлены к бронированию - помечаем их как забронированные
        added_seats = TripSeat.objects.filter(pk__in=pk_set)
        updated_count = 0
        for seat in added_seats:
            if not seat.is_booked:
                seat.is_booked = True
                seat.save(update_fields=['is_booked'])
                updated_count += 1
                logger.debug(f"Marked TripSeat {seat.pk} as booked for Booking {instance.pk}")
            else:
                # Это может произойти, если место уже было забронировано 
                # (хотя валидация должна была это предотвратить)
                logger.warning(f"TripSeat {seat.pk} was already booked when adding to Booking {instance.pk}")
        if updated_count > 0:
            logger.info(f"Marked {updated_count} TripSeat(s) as booked for Booking {instance.pk}")

    elif action == "post_remove" or action == "post_clear":
        # Места были удалены из бронирования - помечаем их как свободные
        # Важно: pk_set передается только для post_remove, для post_clear он пустой.
        # Но для post_clear нам и не нужно знать pk_set, т.к. мы не можем 
        # освободить места, не зная, какие именно были очищены.
        # Стандартное поведение Django при clear() просто удаляет связи.
        # Освобождение мест должно происходить при отмене/удалении бронирования.
        
        # Обрабатываем только post_remove
        if action == "post_remove" and pk_set:
            removed_seats = TripSeat.objects.filter(pk__in=pk_set)
            updated_count = 0
            # Прежде чем освободить место, убедимся, что оно не привязано к ДРУГОМУ АКТИВНОМУ бронированию
            for seat in removed_seats:
                 other_bookings = Booking.objects.filter(trip_seats=seat, is_active=True).exclude(pk=instance.pk)
                 if not other_bookings.exists():
                     if seat.is_booked:
                        seat.is_booked = False
                        seat.save(update_fields=['is_booked'])
                        updated_count += 1
                        logger.debug(f"Marked TripSeat {seat.pk} as unbooked after removing from Booking {instance.pk}")
                 else:
                     logger.warning(f"TripSeat {seat.pk} is still linked to other active bookings, not marking as unbooked.")
                     
            if updated_count > 0:
                 logger.info(f"Marked {updated_count} TripSeat(s) as unbooked after removing from Booking {instance.pk}")


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
    """
    Освобождает места при деактивации бронирования
    """
    # Проверяем, что это существующий объект бронирования
    if instance.pk:
        # Получаем предыдущее состояние объекта
        try:
            previous = Booking.objects.get(pk=instance.pk)
            # Если бронирование становится неактивным
            if previous.is_active and not instance.is_active:
                # Освобождаем места
                for trip_seat in instance.trip_seats.all():
                    trip_seat.is_booked = False
                    trip_seat.save()
        except Booking.DoesNotExist:
            pass

def format_booking(booking):

    local_tz = timezone.get_current_timezone()
    local_time = booking.trip.departure_time.astimezone(local_tz)

    dt = local_time.strftime("%d.%m.%Y %H:%M")
    status = "✅ Активно" if booking.is_active else "❌ Отменено"
    price = booking.total_price
    price_str = f"{int(price)} руб." if price == int(price) else f"{price:.2f} руб."
    seats_info = ", ".join([str(ts.seat.seat_number) for ts in booking.trip_seats.all()])
    text = (
        f"🚖 Новое бронирование создано!\n"
        f"📅 Дата: {dt}\n"
        f"📍 Откуда: {booking.pickup_location}\n"
        f"🏁 Куда: {booking.dropoff_location}\n"
        f"💵 Стоимость: {price_str}\n"
        f"💺 Места: {seats_info if seats_info else 'Не указаны'}\n"
        f"🔹 Статус: {status}"
    )
    return text

def send_telegram_message(chat_id, text):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {'chat_id': chat_id, 'text': text}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки сообщения: {e}")

@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: handle_new_booking(instance))

def handle_new_booking(booking):
    user = booking.user
    if user.chat_id:
        message = format_booking(booking)
        send_telegram_message(user.chat_id, message)



def invalidate_booking_cache(user_id):
    cache_key = f"booking_detailed_{user_id}"
    cache.delete(cache_key)

@receiver(post_save, sender=Booking)
def booking_updated(sender, instance, **kwargs):
    """
    При сохранении бронирования инвалидируем кэш детальной информации для пользователя.
    """
    if instance.user:
        logger.debug(f"Invalidating booking cache for user {instance.user.id}")
        invalidate_booking_cache(instance.user.id)

@receiver(post_delete, sender=Booking)
def booking_deleted(sender, instance, **kwargs):
    """
    При удалении бронирования инвалидируем кэш детальной информации для пользователя.
    """
    if instance.user:
        logger.debug(f"Invalidating booking cache for user {instance.user.id}")
        invalidate_booking_cache(instance.user.id)
