from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.cache import cache

from apps.booking.models import Booking
from apps.seat.models import Seat
from apps.vehicle.models import Vehicle


@receiver(post_save, sender=Vehicle)
def manage_seats(sender, instance, created, **kwargs):
    """
    Функция автоматически создаёт или обновляет места при создании или изменении транспортного средства
    """
    # Получаем текущие места для этого транспортного средства
    current_seats = Seat.objects.filter(vehicle=instance).order_by('seat_number')
    current_seat_count = current_seats.count()

    # Если создано новое транспортное средство
    if created:
        # Создаем места с нуля
        Seat.objects.create(vehicle=instance, seat_number=1, seat_type="front")
        for i in range(instance.total_seats - 1):
            Seat.objects.create(vehicle=instance, seat_number=i + 2, seat_type="back")
    else:
        # Обработка изменения количества мест в существующем транспортном средстве
        if current_seat_count < instance.total_seats:
            # Если количество мест увеличилось, добавляем новые
            for i in range(current_seat_count + 1, instance.total_seats + 1):
                seat_type = "front" if i == 1 else "back"
                Seat.objects.create(vehicle=instance, seat_number=i, seat_type=seat_type)
        elif current_seat_count > instance.total_seats:
            # Если количество мест уменьшилось, удаляем лишние, начиная с конца
            # Получаем список мест, которые нужно удалить
            seats_to_remove = current_seats.order_by('-seat_number')[:current_seat_count - instance.total_seats]

            # Проверяем, есть ли забронированные среди них
            booked_seats = seats_to_remove.filter(is_booked=True)
            if booked_seats.exists():
                # Получаем номера забронированных мест
                booked_numbers = ", ".join(str(seat.seat_number) for seat in booked_seats)
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Нельзя уменьшить количество мест: места {booked_numbers} уже забронированы"
                )

            # Удаляем лишние места (обходим ограничение на удаление мест)
            seats_to_remove.delete()

    # Инвалидируем кэш мест для этого транспортного средства
    cache.delete(f"seats_for_vehicle_{instance.id}")


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