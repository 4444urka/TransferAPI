from rest_framework import serializers

from apps.trip.serializers import TripDetailSerializer
from apps.vehicle.serializers import VehicleSerializer

from .models import Seat, TripSeat


class SeatSerializer(serializers.ModelSerializer):
    vehicle = VehicleSerializer(read_only=True)
    row_index = serializers.IntegerField(read_only=True)
    col_index = serializers.IntegerField(read_only=True)

    class Meta:
        model = Seat
        fields = (
            "id",
            "vehicle",
            "seat_number",
            "seat_class",
            "row_index",
            "col_index",
        )


class TripSeatSerializer(serializers.ModelSerializer):
    row_index = serializers.IntegerField(source="seat.row_index", read_only=True)
    col_index = serializers.IntegerField(source="seat.col_index", read_only=True)

    class Meta:
        model = TripSeat
        fields = (
            "id",
            "trip",
            "seat",
            "seat_class",
            "is_booked",
            "cost",
            "row_index",
            "col_index",
        )
