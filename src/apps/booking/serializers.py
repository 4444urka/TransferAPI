from rest_framework import serializers
from apps.booking.models import Booking

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

        # TODO: Добавить валидацию для сериалайзера