from rest_framework import serializers
from .models import Trip, City
from apps.vehicle.models import Vehicle
from apps.seat.models import Seat

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name')

class VehicleMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('id', 'vehicle_type', 'is_comfort', 'air_conditioning', 'allows_pets', 'license_plate')

class TripListSerializer(serializers.ModelSerializer):
    origin = CitySerializer(read_only=True)
    destination = CitySerializer(read_only=True)
    vehicle = VehicleMinSerializer()
    available_seats = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            'id', 'origin', 'destination', 'departure_time', 'arrival_time',
            'default_ticket_price', 'vehicle', 'available_seats', 'duration'
        )

    def get_available_seats(self, obj):
        total_seats = obj.vehicle.total_seats
        booked_seats = Seat.objects.filter(
            vehicle=obj.vehicle,
            is_booked=True
        ).count()
        return total_seats - booked_seats

    def get_duration(self, obj):
        duration = obj.arrival_time - obj.departure_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}ч {minutes}мин"

class TripDetailSerializer(TripListSerializer):
    """Расширенный сериализатор для детальной информации"""
    seats = serializers.SerializerMethodField()

    class Meta(TripListSerializer.Meta):
        fields = TripListSerializer.Meta.fields + ('seats',)

    def get_seats(self, obj):
        seats = Seat.objects.filter(vehicle=obj.vehicle)
        return [{
            'id': seat.id,
            'number': seat.seat_number,
            'type': seat.seat_type,
            'is_booked': seat.is_booked
        } for seat in seats]

    def get_available_seats(self, obj):
        """Возвращает количество свободных мест"""
        from apps.seat.models import Seat
        return Seat.objects.filter(vehicle=obj.vehicle, is_booked=False).count()