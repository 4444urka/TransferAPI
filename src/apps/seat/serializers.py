from rest_framework import serializers
from .models import Seat, TripSeat


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ('id', 'vehicle', 'seat_number', 'seat_type')


class TripSeatSerializer(serializers.ModelSerializer):
    seat = SeatSerializer(read_only=True)

    class Meta:
        model = TripSeat
        fields = ('id', 'trip', 'seat', 'is_booked', 'cost')