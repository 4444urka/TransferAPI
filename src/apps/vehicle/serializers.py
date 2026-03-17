from rest_framework import serializers
from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    total_seats = serializers.IntegerField(required=False)

    class Meta:
        model = Vehicle
        fields = (
            'id', 'vehicle_type', 'license_plate', 'total_seats',
            'rows', 'seats_per_row', 'is_comfort', 'air_conditioning',
            'allows_pets', 'created_at'
        )
        read_only_fields = ('created_at',)


class VehicleDetailSerializer(VehicleSerializer):
    """Расширенный сериализатор для детальной информации о транспортном средстве"""

    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields


class VehicleMinSerializer(serializers.ModelSerializer):
    """Минимальный сериализатор для использования в связанных моделях"""
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)

    class Meta:
        model = Vehicle
        fields = ('id', 'vehicle_type', 'vehicle_type_display', 'license_plate', 'total_seats', 'rows', 'seats_per_row', 'is_comfort')
        read_only_fields = fields
