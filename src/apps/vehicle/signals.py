from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.seat.models import Seat, TripSeat
from apps.trip.models import Trip
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

        # Также нужно создать TripSeat для каждой поездки с этим транспортным средством
        trips = Trip.objects.filter(vehicle=instance)
        for trip in trips:
            for seat in Seat.objects.filter(vehicle=instance):
                TripSeat.objects.create(trip=trip, seat=seat)
    else:
        # Проверяем изменение количества мест
        if current_seat_count < instance.total_seats:
            # Нужно добавить места
            for i in range(current_seat_count + 1, instance.total_seats + 1):
                seat = Seat.objects.create(vehicle=instance, seat_number=i, seat_type="back")

                # Создать TripSeat для существующих поездок
                trips = Trip.objects.filter(vehicle=instance)
                for trip in trips:
                    TripSeat.objects.create(trip=trip, seat=seat)

        elif current_seat_count > instance.total_seats:
            # Нужно удалить лишние места
            seats_to_remove = current_seats.filter(seat_number__gt=instance.total_seats)

            # Проверяем, есть ли забронированные места среди удаляемых
            booked_seats_exist = TripSeat.objects.filter(
                seat__in=seats_to_remove,
                is_booked=True
            ).exists()

            if booked_seats_exist:
                # Есть забронированные места, которые нельзя удалить
                # Откатываем изменение total_seats
                instance.total_seats = current_seat_count
                instance.save(update_fields=['total_seats'])
                return

            # Удаляем места, начиная с конца
            seats_to_remove.delete()