import logging
from rest_framework import serializers
from apps.booking.models import Booking
from apps.seat.serializers import SeatSerializer
from apps.trip.serializers import TripDetailSerializer
from apps.payment.serializers import PaymentSerializer
from .services import BookingService

logger = logging.getLogger(__name__)

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'trip', 'booking_datetime', 'is_active', 'total_price',
                  'pickup_location', 'dropoff_location']
        read_only_fields = ['booking_datetime', 'user', 'total_price']


class BookingDetailSerializer(serializers.ModelSerializer):
    seat_numbers = serializers.SerializerMethodField()
    trip = TripDetailSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'trip', 'payment', 'booking_datetime',
                  'is_active', 'seat_numbers', 'total_price', 'pickup_location', 'dropoff_location']
        read_only_fields = ['booking_datetime', 'user', 'total_price']
    
    def get_seat_numbers(self, obj):
        return [trip_seat.seat.seat_number for trip_seat in obj.trip_seats.all()]

    def create(self, validated_data):
        return BookingService.create_booking(validated_data, self.initial_data)