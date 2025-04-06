import logging
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from .models import Trip, City
from apps.seat.models import TripSeat

logger = logging.getLogger(__name__)

class TripService:
    """Сервисный слой для работы с поездками"""
    
    def __init__(self, cache_backend=None):
        """Инициализация сервиса с возможностью внедрения зависимостей"""
        self.cache = cache_backend or cache
        self.logger = logging.getLogger(__name__)

    def get_available_seats(self, trip):
        """Получение количества свободных мест для поездки"""
        return TripSeat.objects.filter(trip=trip, is_booked=False).count()

    def get_duration(self, trip):
        """Расчет длительности поездки в формате часы:минуты"""
        duration = trip.arrival_time - trip.departure_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}:{minutes:02d}"

    def get_trip_queryset(self):
        """Получение базового queryset для поездок с оптимизацией"""
        return Trip.objects.select_related(
            'origin', 'destination', 'vehicle'
        )

    def get_cities(self):
        """Получение списка городов с кэшированием"""
        cache_key = 'cities_list'
        cities = self.cache.get(cache_key)
        
        if cities is None:
            cities = list(City.objects.all())
            self.cache.set(cache_key, cities, 60 * 60)  # кэш на 1 час
            self.logger.debug("Cities cache updated")
            
        return cities

    def invalidate_cache(self):
        """Инвалидация кэша поездок"""
        self.cache.delete_pattern('trip_*')
        self.cache.delete('cities_list')
        self.logger.debug("Trip cache invalidated")

    def create_trip(self, validated_data):
        """Создание новой поездки"""
        trip = Trip.objects.create(**validated_data)
        self.invalidate_cache()
        self.logger.info(f"Created new trip: {trip}")
        return trip

    def update_trip(self, trip, validated_data):
        """Обновление поездки"""
        for attr, value in validated_data.items():
            setattr(trip, attr, value)
        trip.save()
        self.invalidate_cache()
        self.logger.info(f"Updated trip: {trip}")
        return trip

    def delete_trip(self, trip):
        """Удаление поездки"""
        trip.delete()
        self.invalidate_cache()
        self.logger.info(f"Deleted trip: {trip}") 