from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q
from .models import Trip

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'

    def validate_departure_time(self, value):
        """Проверка что время отправления не в прошлом"""
        if value < timezone.now():
            raise serializers.ValidationError("Время отправления не может быть в прошлом")
        return value

    def validate_default_ticket_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        return value

    def validate(self, data):
        departure = data['departure_time']
        arrival = data['arrival_time']
        vehicle = data['vehicle']

        if arrival <= departure:
            raise serializers.ValidationError("Время прибытия должно быть позже отправления")

        # Проверка пересечений временных интервалов
        conflicts = Trip.objects.filter(vehicle=vehicle).filter(
            Q(departure_time__lt=arrival, arrival_time__gt=departure)
        ).exclude(pk=self.instance.pk if self.instance else None)

        if conflicts.exists():
            raise serializers.ValidationError("Транспорт уже занят в этот период")

        return data