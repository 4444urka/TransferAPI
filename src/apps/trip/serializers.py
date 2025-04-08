from rest_framework import serializers
from apps.trip.models import Trip, City
from apps.vehicle.serializers import VehicleMinSerializer
from .services.CityService import CityService
from .services.TripService import TripService


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
    origin_name = serializers.CharField(write_only=True, required=True)
    destination_name = serializers.CharField(write_only=True, required=True)
    city_service = CityService()
    
    class Meta:
        model = Trip
        fields = (
            'id', 'vehicle', 'origin', 'destination',
            'departure_time', 'arrival_time', 'default_ticket_price',
            'origin_name', 'destination_name'
        )
        read_only_fields = ('origin', 'destination')
        
    def validate(self, data):
        """
        Проверка на существование городов и валидация данных
        """
        origin_name = data.get('origin_name')
        destination_name = data.get('destination_name')
        
        # Проверяем что города отправления и назначения не совпадают
        if origin_name == destination_name:
            raise serializers.ValidationError("Город отправления и назначения не могут совпадать")
        
        return data
        
    def create(self, validated_data):
        """
        Создание поездки с указанными названиями городов
        """
        origin_name = validated_data.pop('origin_name')
        destination_name = validated_data.pop('destination_name')
        
        try:
            origin = self.city_service.get_by_name(origin_name)
            destination = self.city_service.get_by_name(destination_name)
        except Exception as e:
            raise serializers.ValidationError(f"Ошибка при получении городов: {e}")

        validated_data['origin'] = origin
        validated_data['destination'] = destination
        
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        """
        Обновление поездки с указанными названиями городов
        """
        if 'origin_name' in validated_data:
            origin_name = validated_data.pop('origin_name')
            try:
                origin = self.city_service.get_by_name(origin_name)
            except Exception as e:
                raise serializers.ValidationError(f"Ошибка при получении города отправления: {e}")
            validated_data['origin'] = origin
            
        if 'destination_name' in validated_data:
            destination_name = validated_data.pop('destination_name')
            try:
                destination = self.city_service.get_by_name(destination_name)
            except Exception as e:
                raise serializers.ValidationError(f"Ошибка при получении города назначения: {e}")
            validated_data['destination'] = destination
            
        return super().update(instance, validated_data)