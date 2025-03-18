from rest_framework import serializers
from apps.booking.models import Booking
from apps.trip.models import Trip
from apps.seat.models import Seat, TripSeat
from apps.seat.serializers import SeatSerializer
from apps.trip.serializers import TripDetailSerializer
from apps.payment.serializers import PaymentSerializer



class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'trip', 'booking_datetime', 'is_active', 'total_price',
                  'pickup_location', 'dropoff_location']
        read_only_fields = ['booking_datetime', 'user', 'total_price']


class BookingDetailSerializer(serializers.ModelSerializer):
    seats = SeatSerializer(many=True, read_only=True)
    trip = TripDetailSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'trip', 'payment', 'booking_datetime',
                  'is_active', 'seats', 'total_price', 'pickup_location', 'dropoff_location']
        read_only_fields = ['booking_datetime', 'user', 'total_price']

    def create(self, validated_data):
        trip_id = self.initial_data.get('trip_id')
        seats_ids = self.initial_data.get('seats_ids', [])

        if not trip_id:
            raise serializers.ValidationError({"trip_id": "Необходимо указать ID поездки"})

        if not seats_ids:
            raise serializers.ValidationError({"seats_ids": "Необходимо выбрать хотя бы одно место"})

        trip = Trip.objects.get(pk=trip_id)
        validated_data['trip'] = trip

        trip_seats = TripSeat.objects.filter(trip_id=trip_id, seat_id__in=seats_ids, is_booked=False)

        # Проверяем, что все места доступны
        if trip_seats.count() != len(seats_ids):
            # Находим недоступные места
            available_seat_ids = [ts.seat_id for ts in trip_seats]
            unavailable_ids = [s_id for s_id in seats_ids if s_id not in available_seat_ids]
            raise serializers.ValidationError(
                {"seats_ids": f"Места с ID {', '.join(map(str, unavailable_ids))} недоступны для бронирования"}
            )

        # Создаем бронирование
        booking = Booking.objects.create(**validated_data)

        # Бронируем места
        for trip_seat in trip_seats:
            trip_seat.is_booked = True
            trip_seat.save()
            booking.trip_seats.add(trip_seat)

        return booking