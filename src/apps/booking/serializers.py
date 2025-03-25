import logging
from rest_framework import serializers
from apps.booking.models import Booking
from apps.trip.models import Trip
from apps.seat.models import Seat, TripSeat
from apps.seat.serializers import SeatSerializer
from apps.trip.serializers import TripDetailSerializer
from apps.payment.serializers import PaymentSerializer

logger = logging.getLogger(__name__)

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'trip', 'booking_datetime', 'is_active', 'total_price',
                  'pickup_location', 'dropoff_location']
        read_only_fields = ['booking_datetime', 'user', 'total_price']


class BookingDetailSerializer(serializers.ModelSerializer):
    seats = SeatSerializer(many=True, read_only=True)
    trip = TripDetailSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'trip', 'payment', 'booking_datetime',
                  'is_active', 'seats', 'total_price', 'pickup_location', 'dropoff_location']
        read_only_fields = ['booking_datetime', 'user', 'total_price']

    def create(self, validated_data):
        logger.debug("Creating new booking")
        trip_id = self.initial_data.get('trip_id')
        seat_numbers = self.initial_data.get('seat_numbers', [])

        if not trip_id:
            logger.error("Trip ID is required")
            raise serializers.ValidationError({"trip_id": "Необходимо указать ID поездки"})

        if not seat_numbers:
            logger.error("seat numbers required")
            raise serializers.ValidationError({"seat_numbers": "Необходимо выбрать хотя бы одно место"})

        trip = Trip.objects.get(pk=trip_id)
        validated_data['trip'] = trip

        trip_seats = TripSeat.objects.filter(trip_id=trip_id, seat__seat_number__in=seat_numbers, is_booked=False)

        # Проверяем, что все места доступны
        if trip_seats.count() != len(seat_numbers):
            # Находим недоступные места
            available_seat_ids = [ts.seat_id for ts in trip_seats]
            unavailable_ids = [s_id for s_id in seat_numbers if s_id not in available_seat_ids]
            logger.error("Some seats are not available")
            raise serializers.ValidationError(
                {"seat_numbers": f"Места с номером {', '.join(map(str, unavailable_ids))} недоступны для бронирования"}
            )

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