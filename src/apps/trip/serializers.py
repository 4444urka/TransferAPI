from rest_framework import serializers
from apps.trip.models import Trip, City
from apps.vehicle.serializers import VehicleMinSerializer
from .services.CityService import CityService
from .services.TripService import TripService


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name')

class TripDetailSerializer(serializers.ModelSerializer):
    from_city = CitySerializer(read_only=True)
    to_city = CitySerializer(read_only=True)
    vehicle = VehicleMinSerializer(read_only=True)
    available_seats = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            'id', 'from_city', 'to_city', 'departure_time', 'arrival_time',
            'front_seat_price', 'middle_seat_price', 'back_seat_price',
            'vehicle', 'available_seats', 'duration',
            'booking_cutoff_minutes', 'is_bookable'
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
    from_city_name = serializers.CharField(write_only=True, required=True)
    to_city_name = serializers.CharField(write_only=True, required=True)
    city_service = CityService()
    
    class Meta:
        model = Trip
        fields = (
            'id', 'vehicle', 'from_city', 'to_city',
            'departure_time', 'arrival_time',
            'front_seat_price', 'middle_seat_price', 'back_seat_price',
            'from_city_name', 'to_city_name', 'booking_cutoff_minutes', 'is_bookable'
        )
        read_only_fields = ('from_city', 'to_city')
        
    def validate(self, data):
        """
        Проверка на существование городов и валидация данных
        """
        from_city_name = data.get('from_city_name')
        to_city_name = data.get('to_city_name')
        
        # Проверяем что города отправления и назначения не совпадают
        if from_city_name == to_city_name:
            raise serializers.ValidationError("Город отправления и назначения не могут совпадать")
        
        return data
        
    def create(self, validated_data):
        """
        Создание поездки с указанными названиями городов
        """
        from_city_name = validated_data.pop('from_city_name')
        to_city_name = validated_data.pop('to_city_name')
        
        try:
            from_city = self.city_service.get_by_name(from_city_name)
            to_city = self.city_service.get_by_name(to_city_name)
        except Exception as e:
            raise serializers.ValidationError(f"Ошибка при получении городов: {e}")

        validated_data['from_city'] = from_city
        validated_data['to_city'] = to_city
        
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        """
        Обновление поездки с указанными названиями городов
        """
        if 'from_city_name' in validated_data:
            from_city_name = validated_data.pop('from_city_name')
            try:
                from_city_name = self.city_service.get_by_name(from_city_name)
            except Exception as e:
                raise serializers.ValidationError(f"Ошибка при получении города отправления: {e}")
            validated_data['from_city'] = from_city_name
            
        if 'to_city_name' in validated_data:
            to_city_name = validated_data.pop('to_city_name')
            try:
                to_city = self.city_service.get_by_name(to_city_name)
            except Exception as e:
                raise serializers.ValidationError(f"Ошибка при получении города назначения: {e}")
            validated_data['to_city'] = to_city
            
        return super().update(instance, validated_data)