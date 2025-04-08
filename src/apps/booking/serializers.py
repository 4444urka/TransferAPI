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
        return BookingService.create_booking(validated_data, self.initial_data)