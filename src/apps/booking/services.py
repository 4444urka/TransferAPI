import logging
from django.core.exceptions import ValidationError
from rest_framework import serializers
from apps.booking.models import Booking
from apps.trip.models import Trip
from apps.seat.models import TripSeat
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class BookingService:
    
    def check_seats_availability(trip_id, seat_numbers):
        """Проверка доступности мест для бронирования"""
        trip_seats = TripSeat.objects.filter(trip_id=trip_id, seat__seat_number__in=seat_numbers, is_booked=False)
        
        if trip_seats.count() != len(seat_numbers):
            available_seat_ids = [ts.seat_id for ts in trip_seats]
            unavailable_ids = [s_id for s_id in seat_numbers if s_id not in available_seat_ids]
            raise ValidationError(
                f"Места с номером {', '.join(map(str, unavailable_ids))} недоступны для бронирования"
            )
        return trip_seats

    def calculate_booking_price(trip, seat_numbers):
        """Расчет стоимости бронирования"""
        total_price = 0
        for seat_number in seat_numbers:
            trip_seat = TripSeat.objects.get(trip=trip, seat__seat_number=seat_number)
            seat = trip_seat.seat
            # TODO: Пока что за переднее место надбавка 20%
            multiplier = 1.2 if seat.seat_type == "front" else 1.0
            total_price += round(trip.default_ticket_price * multiplier)
        return total_price

    def get_user_bookings(user):
        """Получение списка бронирований с учетом прав доступа"""
        if not user or not user.is_authenticated:
            return Booking.objects.none()
        if user.has_perm('booking.can_view_all_booking') or user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=user)

    def create_booking(validated_data, initial_data):
        """Создание нового бронирования"""
        logger.debug("Creating new booking")
        trip_id = initial_data.get('trip_id')
        seat_numbers = initial_data.get('seat_numbers', [])

        if not trip_id:
            logger.error("Trip ID is required")
            raise serializers.ValidationError({"trip_id": "Необходимо указать ID поездки"})

        if not seat_numbers:
            logger.error("seat numbers required")
            raise serializers.ValidationError({"seat_numbers": "Необходимо выбрать хотя бы одно место"})

        trip = Trip.objects.get(pk=trip_id)
        validated_data['trip'] = trip

        # Проверяем доступность мест
        trip_seats = BookingService.check_seats_availability(trip_id, seat_numbers)

        # Создаем бронирование
        booking = Booking.objects.create(**validated_data)
        logger.info(f"Created new booking: {booking}")

        # Бронируем места
        logger.debug("Booking some seats")
        for trip_seat in trip_seats:
            trip_seat.is_booked = True
            trip_seat.save()
            booking.trip_seats.add(trip_seat)
            
        logger.info("Seats successfully booked")

        return booking

    def cancel_booking(booking):
        """Отмена бронирования"""
        if not booking.is_active:
            raise ValidationError("Бронирование уже отменено")

        # Отмечаем бронирование как неактивное
        booking.is_active = False
        booking.save()

        # Освобождаем места
        for trip_seat in booking.trip_seats.all():
            trip_seat.is_booked = False
            trip_seat.save()

        return booking