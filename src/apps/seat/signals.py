from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.booking.models import Booking
from apps.seat.models import Seat
from apps.vehicle.models import Vehicle


@receiver(post_save, sender=Vehicle)
def create_seats(sender, instance, created, **kwargs):
    """
    Функция автоматически создаёт места при создании транспортного средства
    """
    if created:
        # TODO: Пока что одно переднее место и остальные задние
        Seat.objects.create(vehicle=instance, seat_number=1, seat_type="front")
        for i in range(instance.total_seats - 1):
            Seat.objects.create(vehicle=instance, seat_number=i+2, seat_type="back")

# TODO: Исправить костыль
"""
На данный момент, бронирование мест работает через флаг is_booked у места. Это хуйня какая-то так как из за этого
 приходится добавляять listener, который освобождает место при выполнении заказа (То есть когда заказ становится неактивным)
 Пока что я считаю что это костыль так как я уверен что это можно переделать намного лучше.
"""
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