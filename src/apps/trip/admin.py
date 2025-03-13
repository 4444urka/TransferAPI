from django.contrib import admin
from django import forms
from .models import Trip, City

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

class TripAdminForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = '__all__'

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'origin', 'destination', 'departure_time', 'arrival_time', 'default_ticket_price')
    list_filter = ('vehicle', 'origin', 'destination', 'departure_time')
    search_fields = ('vehicle__license_plate', 'origin__name', 'destination__name')
    fieldsets = (
        (None, {
            'fields': ('vehicle', 'origin', 'destination')
        }),
        ('Время', {
            'fields': (('departure_time', 'arrival_time'),),
            'description': '<div class="help">Все времена указываются в часовом поясе сервера (UTC+10)</div>'
        }),
        ('Цена', {
            'fields': ('default_ticket_price',)
        }),
    )

    def formatted_departure(self, obj):
        return obj.departure_time.strftime('%Y-%m-%d %H:%M')
    formatted_departure.short_description = 'Дата и время отправления'

    def formatted_arrival(self, obj):
        return obj.arrival_time.strftime('%Y-%m-%d %H:%M')
    formatted_arrival.short_description = 'Дата и время прибытия'

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean() 
            super().save_model(request, obj, form, change)
        except forms.ValidationError as e:
            form.add_error(None, e) 