from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from apps.trip.models import Trip


class TripAdminForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = '__all__'


class TripAdmin(admin.ModelAdmin):
    form = TripAdminForm
    list_display = ('date', 'departure_time', 'origin', 'destination', 'arrival_time', 'default_ticket_price', 'vehicle')
    list_filter = ('date', 'origin', 'destination', 'vehicle')
    search_fields = ('origin', 'destination')
    fieldsets = (
        (None, {
            'fields': (('date', 'departure_time', 'arrival_time'),
                      ('origin', 'destination'),
                      'default_ticket_price',
                      'vehicle')
        }),
    )


admin.site.register(Trip, TripAdmin)
