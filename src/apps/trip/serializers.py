from rest_framework import serializers
from apps.trip.models import Trip, City
from apps.vehicle.serializers import VehicleMinSerializer
from .services import TripService


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
            'default_ticket_price', 'vehicle', 'available_seats', 'duration'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip_service = TripService()

    def get_available_seats(self, obj):
        """Получение количества свободных мест для поездки"""
        return self.trip_service.get_available_seats(obj)

    def get_duration(self, obj):
        """Получение длительности поездки в формате часы:минуты"""
        return self.trip_service.get_duration(obj)


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
            'default_ticket_price', 'vehicle', 'available_seats', 'duration'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip_service = TripService()

    def get_available_seats(self, obj):
        """Получение количества свободных мест для поездки"""
        return self.trip_service.get_available_seats(obj)

    def get_duration(self, obj):
        """Получение длительности поездки в формате часы:минуты"""
        return self.trip_service.get_duration(obj)


# Сериализатор для создания/редактирования поездок
class TripCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = (
            'id', 'vehicle', 'origin', 'destination',
            'departure_time', 'arrival_time', 'default_ticket_price'
        )