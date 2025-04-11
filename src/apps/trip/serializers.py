from rest_framework import serializers
from apps.trip.models import Trip, City
from apps.vehicle.serializers import VehicleMinSerializer
from apps.seat.models import TripSeat


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name')


class TripListSerializer(serializers.ModelSerializer):
    origin = CitySerializer(read_only=True)
    destination = CitySerializer(read_only=True)
    vehicle = VehicleMinSerializer(read_only=True)
    available_seats = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            'id', 'origin', 'destination', 'departure_time', 'arrival_time',
            'default_ticket_price', 'vehicle', 'available_seats', 'duration',
            'booking_cutoff_minutes', 'is_bookable'
        )

    def get_available_seats(self, obj):
        """Получение количества свободных мест для поездки"""
        total_seats = obj.vehicle.total_seats
        booked_seats = TripSeat.objects.filter(
            trip=obj,
            is_booked=True
        ).count()
        return total_seats - booked_seats

    def get_duration(self, obj):
        """Получение длительности поездки в формате часы:минуты"""
        duration = obj.arrival_time - obj.departure_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}ч {minutes}мин"


class TripDetailSerializer(serializers.ModelSerializer):
    origin = CitySerializer(read_only=True)
    destination = CitySerializer(read_only=True)
    vehicle = VehicleMinSerializer(read_only=True)
    available_seats = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            'id', 'origin', 'destination', 'departure_time', 'arrival_time',
            'default_ticket_price', 'vehicle', 'available_seats', 'duration',
            'booking_cutoff_minutes', 'is_bookable'
        )

    def get_available_seats(self, obj):
        """Получение количества свободных мест для поездки"""
        return TripSeat.objects.filter(trip=obj, is_booked=False).count()

    def get_duration(self, obj):
        """Получение длительности поездки в формате часы:минуты"""
        duration = obj.arrival_time - obj.departure_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}ч {minutes}мин"


# Сериализатор для создания/редактирования поездок
class TripCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = (
            'id', 'vehicle', 'origin', 'destination',
            'departure_time', 'arrival_time', 'default_ticket_price',
            'booking_cutoff_minutes', 'is_bookable'
        )