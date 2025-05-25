from django.contrib import admin
from django import forms
from .models import Trip, City
from apps.auth.models import User

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
    list_display = ('vehicle', 'from_city', 'to_city', 'departure_time', 'arrival_time', 'front_seat_price', 'middle_seat_price', 'back_seat_price', 'is_bookable', 'booking_cutoff_minutes', 'driver')
    list_filter = ('vehicle', 'from_city', 'to_city', 'departure_time', 'is_bookable', 'driver')
    search_fields = ('vehicle__license_plate', 'from_city__name', 'to_city__name', 'is_bookable')
    fieldsets = (
        (None, {
            'fields': ('vehicle', 'driver', 'from_city', 'to_city')
        }),
        ('Время', {
            'fields': (('departure_time', 'arrival_time'),),
            'description': '<div class="help">Все времена указываются в часовом поясе сервера (UTC+10)</div>'
        }),
        ('Цена', {
            'fields': ('front_seat_price', 'middle_seat_price', 'back_seat_price')
        }),
        ('Дополнительные данные', {
            'fields': ('is_bookable', 'booking_cutoff_minutes'),
            'description': 'Поля, связанные с возможностью бронирования: is_bookable определяет, можно ли сделать бронирование, а booking_cutoff_minutes – время до отправления, после которого бронирование закрывается.'

        })
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "driver":
            kwargs["queryset"] = User.objects.filter(groups__name='Водитель')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)