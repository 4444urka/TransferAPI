import logging
from django.core.exceptions import ValidationError
from rest_framework import serializers
from apps.booking.models import Booking
from apps.trip.models import Trip
from apps.seat.models import TripSeat
from django.contrib.auth import get_user_model
from utils.address import find_address_by_name
from apps.payment.models import Payment

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
            multiplier = 1.2 if seat.price_zone == "front" else 1.0
            total_price += round(trip.default_ticket_price * multiplier)
        return total_price

    def get_user_bookings(user):
        """Получение списка бронирований с учетом прав доступа"""
        if not user or not user.is_authenticated:
            return Booking.objects.none()
        # Возвращаем все бронирования для администраторов и пользователей с правом просмотра
        if user.has_perm('booking.can_view_all_booking') or user.is_staff:
            return Booking.objects.all()
        # Для обычных пользователей показываем только их бронирования
        return Booking.objects.filter(user=user)

    def create_booking(validated_data, initial_data):
        """Создание нового бронирования"""
        logger.debug("Creating new booking")
        trip_id = initial_data.get('trip_id')
        seat_numbers = initial_data.get('seat_numbers', [])
        pickup_location = initial_data.get('pickup_location', '')
        dropoff_location = initial_data.get('dropoff_location', '')
        payment_data = initial_data.get('payment', {})

        if not trip_id:
            logger.error("Trip ID is required")
            raise serializers.ValidationError({"trip_id": "Необходимо указать ID поездки"})

        if not seat_numbers:
            logger.error("seat numbers required")
            raise serializers.ValidationError({"seat_numbers": "Необходимо выбрать хотя бы одно место"})


        if payment_data:
            try:
                payment = Payment.objects.get(pk=payment_data.get('id'))
                validated_data['payment'] = payment
            except Payment.DoesNotExist:
                logger.error(f"Payment with ID {payment_data.get('id')} not found")
                raise serializers.ValidationError({"payment": f"Оплата с ID {payment_data.get('id')} не найдена"})

        try:
            trip = Trip.objects.get(pk=trip_id)
        except Trip.DoesNotExist:
            logger.error(f"Trip with ID {trip_id} not found")
            raise serializers.ValidationError({"trip_id": f"Поездка с ID {trip_id} не найдена"})

        # Проверяем, доступна ли поездка для бронирования
        if not trip.is_bookable:
            logger.error(f"Trip with ID {trip_id} is not bookable")
            raise serializers.ValidationError({"trip_id": "Эта поездка недоступна для бронирования"})

        validated_data['trip'] = trip
        
        # Проверка адреса посадки
        if not pickup_location:
            logger.error("Pickup location is required")
            raise serializers.ValidationError({"pickup_location": "Необходимо указать место посадки"})
            
        try:
            refactored_pickup = find_address_by_name(pickup_location, trip.from_city.name)
            if not refactored_pickup:
                logger.error(f"Invalid pickup location: {pickup_location}")
                raise serializers.ValidationError({"pickup_location": f"Адрес '{pickup_location}' не найден в городе {trip.from_city.name}"})
            validated_data['pickup_location'] = refactored_pickup
        except Exception as e:
            logger.error(f"Error validating pickup location: {str(e)}")
            raise serializers.ValidationError({"pickup_location": f"Ошибка проверки адреса посадки: {str(e)}"})
        
        # Проверка адреса высадки
        if not dropoff_location:
            logger.error("Dropoff location is required")
            raise serializers.ValidationError({"dropoff_location": "Необходимо указать место высадки"})
            
        try:
            refactored_dropoff = find_address_by_name(dropoff_location, trip.to_city.name)
            if not refactored_dropoff:
                logger.error(f"Invalid dropoff location: {dropoff_location}")
                raise serializers.ValidationError({"dropoff_location": f"Адрес '{dropoff_location}' не найден в городе {trip.to_city.name}"})
            validated_data['dropoff_location'] = refactored_dropoff
        except Exception as e:
            logger.error(f"Error validating dropoff location: {str(e)}")
            raise serializers.ValidationError({"dropoff_location": f"Ошибка проверки адреса высадки: {str(e)}"})

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