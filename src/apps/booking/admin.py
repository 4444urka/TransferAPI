from django import forms
from django.contrib import admin
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Booking
from apps.seat.models import Seat


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'

    def clean_seats(self):
        """Проверяет места непосредственно в поле формы"""
        seats = self.cleaned_data.get('seats')
        trip = self.cleaned_data.get('trip')

        if not seats or not trip:
            return seats

        for seat in seats:
            # Проверка принадлежности места к транспортному средству рейса
            if seat.vehicle != trip.vehicle:
                raise forms.ValidationError(f"Место {seat} не соответствует транспортному средству рейса")

            # Проверка, не забронировано ли уже место (и не в текущем бронировании при редактировании)
            if seat.is_booked:
                instance_id = self.instance.id if self.instance else None
                if not instance_id or not Booking.objects.filter(id=instance_id, seats=seat).exists():
                    raise forms.ValidationError(f"Место {seat} уже забронировано")

        return seats

    def clean(self):
        """Проверяет всю форму, включая сумму платежа"""
        cleaned_data = super().clean()
        payment = cleaned_data.get('payment')
        seats = cleaned_data.get('seats')
        trip = cleaned_data.get('trip')

        # Если нет платежа или отсутствуют необходимые данные, вернуть
        if not payment or not seats or not trip:
            return cleaned_data

        # Расчет цены на основе данных формы
        calculated_total = Decimal(0)
        if self.instance.pk:  # Для существующих бронирований
            calculated_total = self.instance.total_price
        else:  # Для новых бронирований
            for seat in seats:
                multiplier = Decimal(1.2) if seat.seat_type == "front" else Decimal(1.0)
                calculated_total += round(trip.default_ticket_price * multiplier)

        # Сравнение округленных значений во избежание проблем с плавающей точкой
        if round(payment.amount, 2) != round(calculated_total, 2):
            self.add_error('payment',
                f"Сумма платежа ({payment.amount}) не соответствует общей стоимости ({calculated_total})")

        return cleaned_data


class BookingAdmin(admin.ModelAdmin):
    form = BookingForm
    list_display = ('id', 'user', 'trip', 'booking_datetime', 'total_price', 'payment', 'is_active')
    list_filter = ('is_active', 'booking_datetime')
    search_fields = ('user__phone_number', 'trip__departure_time')

    def save_model(self, request, obj, form, change):
        """Переопределяет для гарантии соблюдения валидации формы"""
        if form.is_valid():
            super().save_model(request, obj, form, change)


admin.site.register(Booking, BookingAdmin)