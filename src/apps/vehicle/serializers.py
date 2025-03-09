from rest_framework import serializers
from apps.vehicle.models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'vehicle_type', 'license_plate', 'total_seats',
                 'is_comfort', 'air_conditioning', 'allows_pets', 'created_at']
        read_only_fields = ['created_at']