from rest_framework import serializers
from .models import Trip, City
from apps.vehicle.serializers import VehicleSerializer


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name']


class TripDetailSerializer(serializers.ModelSerializer):
    origin = CitySerializer(read_only=True)
    destination = CitySerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'origin', 'destination', 'departure_time', 'arrival_time',
                  'vehicle', 'default_ticket_price', 'available_seats']

    def get_available_seats(self, obj):
        """Возвращает количество свободных мест"""
        from apps.seat.models import Seat
        return Seat.objects.filter(vehicle=obj.vehicle, is_booked=False).count()