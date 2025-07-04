from django import forms
from django.contrib import admin
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Booking
from apps.seat.models import Seat, TripSeat
from utils.address import find_address_by_name
from apps.trip.models import Trip

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk and self.instance.trip:
             self.fields['trip_seats'].queryset = TripSeat.objects.filter(trip=self.instance.trip)
        elif 'trip' in self.initial:
            try:
                trip_id = self.initial['trip']
                trip = Trip.objects.get(pk=trip_id)
                self.fields['trip_seats'].queryset = TripSeat.objects.filter(trip=trip)
            except (Trip.DoesNotExist, ValueError, TypeError):
                # Если trip не найден или некорректен, оставляем queryset по умолчанию или делаем пустым
                # JS все равно его очистит, если trip не будет выбран
                self.fields['trip_seats'].queryset = TripSeat.objects.none()
        else:
            # При добавлении, если trip не выбран, JS должен очистить поле
             self.fields['trip_seats'].queryset = TripSeat.objects.none()

    def clean_trip_seats(self):
        trip = self.cleaned_data.get('trip')
        trip_seats = self.cleaned_data.get('trip_seats')

        if trip and trip_seats:
            for trip_seat in trip_seats:
                if trip_seat.trip != trip:
                    raise ValidationError(
                        f"Место {trip_seat.seat} не принадлежит выбранной поездке {trip}."
                    )
        return trip_seats

    # Добавляем общий метод clean для проверки суммы платежа
    def clean(self):
        cleaned_data = super().clean()
        payment = cleaned_data.get('payment')
        trip = cleaned_data.get('trip')
        trip_seats = cleaned_data.get('trip_seats')

        # Проверяем только если все нужные поля заполнены
        if payment and trip and trip_seats:
            # Рассчитываем ожидаемую стоимость на основе данных формы
            expected_total_price = Decimal(0)
            for trip_seat in trip_seats:
                seat = trip_seat.seat
                # Используем ту же логику расчета, что и в модели
                
                if seat.price_zone == "front":
                    expected_total_price += trip.front_seat_price
                elif seat.price_zone == "middle":
                    expected_total_price += trip.middle_seat_price
                elif seat.price_zone == "back":
                    expected_total_price += trip.back_seat_price

            
            # Сравниваем сумму платежа с рассчитанной стоимостью
            if payment.amount != expected_total_price:
                raise ValidationError(
                    f"Сумма платежа ({payment.amount}) не соответствует рассчитанной общей стоимости ({expected_total_price}) для выбранных мест."
                )

        return cleaned_data


class BookingAdmin(admin.ModelAdmin):
    form = BookingForm
    list_display = ('id', 'user', 'trip', 'pickup_location', 'dropoff_location', 'booking_datetime', 'total_price', 'payment', 'is_active')
    list_filter = ('is_active', 'booking_datetime')
    search_fields = ('user__phone_number', 'trip__departure_time')

    class Media:
        js = ('admin/js/booking_admin.js',) 

admin.site.register(Booking, BookingAdmin)