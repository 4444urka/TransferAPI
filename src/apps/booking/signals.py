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
