from django import forms
from django.contrib import admin
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Booking
from apps.seat.models import Seat
from utils.address import find_street_by_name

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'  


class BookingAdmin(admin.ModelAdmin):
    form = BookingForm
    list_display = ('id', 'user', 'trip', 'pickup_location', 'dropoff_location', 'booking_datetime', 'total_price', 'payment', 'is_active')
    list_filter = ('is_active', 'booking_datetime')
    search_fields = ('user__phone_number', 'trip__departure_time')


admin.site.register(Booking, BookingAdmin)