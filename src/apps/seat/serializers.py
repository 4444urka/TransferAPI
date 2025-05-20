from rest_framework import serializers

from apps.trip.serializers import TripDetailSerializer
from apps.vehicle.serializers import VehicleSerializer
from .models import Seat, TripSeat


class SeatSerializer(serializers.ModelSerializer):
    
    vehicle = VehicleSerializer(read_only=True)
    
    class Meta:
        model = Seat
        fields = ('id', 'vehicle', 'seat_number', 'price_zone')

    
class TripSeatSerializer(serializers.ModelSerializer):
    seat = SeatSerializer(read_only=True)
    trip = TripDetailSerializer(read_only=True)

    class Meta:
        model = TripSeat
        fields = ('id', 'trip', 'seat', 'is_booked', 'cost')