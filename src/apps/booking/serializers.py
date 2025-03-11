from rest_framework import serializers
from apps.booking.models import Booking
from apps.trip.models import Trip
from apps.seat.models import Seat
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

        # Получаем места по указанным ID
        seats = Seat.objects.filter(id__in=seats_ids)

        # Проверяем, что все ID мест действительно существуют
        if len(seats) != len(seats_ids):
            # Находим несуществующие ID
            found_ids = [seat.id for seat in seats]
            missing_ids = [seat_id for seat_id in seats_ids if seat_id not in found_ids]
            raise serializers.ValidationError(
                {"seats_ids": f"Места с ID {', '.join(map(str, missing_ids))} не существуют"})

        # Проверяем занятость мест до создания бронирования
        for seat in seats:
            # Проверка, что место относится к нужному транспорту
            if seat.vehicle != trip.vehicle:
                raise serializers.ValidationError(
                    {"seats_ids": f"Место {seat} не соответствует транспортному средству рейса"})

            # Проверка занятости
            if seat.is_booked:
                raise serializers.ValidationError({"seats_ids": f"Место {seat} уже забронировано"})

        # Создаем бронирование
        booking = Booking.objects.create(**validated_data)

        # Добавляем места
        booking._seats_to_validate = seats  # Для проверки в clean()
        booking.seats.set(seats)

        return booking