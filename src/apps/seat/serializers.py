from rest_framework import serializers
from apps.seat.models import Seat

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id', 'vehicle', 'seat_number', 'seat_type', 'is_booked']
        read_only_fields = ['is_booked']