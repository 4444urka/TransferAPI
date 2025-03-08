from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from apps.trip.models import Trip


class TripAdminForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()

        departure_time = cleaned_data.get('departure_time')
        arrival_time = cleaned_data.get('arrival_time')
        if departure_time and arrival_time and departure_time >= arrival_time:
            raise ValidationError("Время отправления должно быть раньше времени прибытия.")
        
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        if origin and destination and origin == destination:
            raise ValidationError("Пункт отправления и пункт назначения не должны совпадать.")
        
        return cleaned_data


class TripAdmin(admin.ModelAdmin):
    form = TripAdminForm
    list_display = ('date', 'departure_time', 'origin', 'destination', 'arrival_time', 'default_ticket_price')
    list_filter = ('date', 'origin', 'destination')
    search_fields = ('origin', 'destination')
    fieldsets = (
        (None, {
            'fields': (('date', 'departure_time', 'arrival_time'), ('origin', 'destination'), 'default_ticket_price')
        }),
    )


admin.site.register(Trip, TripAdmin)
