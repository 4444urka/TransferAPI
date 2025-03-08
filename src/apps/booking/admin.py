from decimal import Decimal

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Booking


class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем наличие пользователя
        if not cleaned_data.get('user'):
            raise forms.ValidationError("Пользователь обязателен")

        seats = cleaned_data.get('seats', [])
        for seat in seats:

            # Проверяем принадлежит ли выбранное место транспортному средству рейса
            if seat.vehicle != cleaned_data.get('trip').vehicle:
                raise forms.ValidationError(f"Место {seat} не соответствует транспортному средству рейса")

            # Проверяем, не занято ли уже это место в другом бронировании
            if seat.is_booked:
                # Проверяем, не принадлежит ли это место текущему бронированию
                if hasattr(self.instance, 'pk') and self.instance.pk:
                    current_booking_seats = self.instance.seats.all()
                    if seat not in current_booking_seats:
                        raise forms.ValidationError(f"Место {seat} уже забронировано")
                else:
                    raise forms.ValidationError(f"Место {seat} уже забронировано")

        # Проверка платежа, если он указан
        payment = cleaned_data.get('payment')
        if payment is not None:
            # Рассчитываем total_price на основе выбранных в форме мест
            seats = cleaned_data.get('seats', [])
            trip = cleaned_data.get('trip')
            if trip:
                total_price = Decimal(0)
                for seat in seats:
                    multiplier = Decimal(1.2) if seat.seat_type == "front" else Decimal(1.0)
                    total_price += round(trip.default_ticket_price * multiplier)

                if payment.amount != total_price:
                    raise forms.ValidationError(
                        f"Сумма платежа ({payment.amount}) не соответствует общей стоимости ({total_price})"
                    )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Явно устанавливаем пользователя из формы
        if 'user' in self.cleaned_data:
            instance.user = self.cleaned_data['user']

        # Обновляем статус забронированности мест
        seats = self.cleaned_data.get('seats', [])
        for seat in seats:
            seat.is_booked = True
            seat.save()

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ('id', 'user', 'trip', 'booking_datetime', 'total_price', 'payment', 'is_active')
    list_filter = ('is_active', 'booking_datetime')
    search_fields = ('user__phone_number', 'trip__departure_time')

    def save_model(self, request, obj, form, change):
        if not obj.user:
            raise ValidationError("Booking must have a user")
        super().save_model(request, obj, form, change)


admin.site.register(Booking, BookingAdmin)