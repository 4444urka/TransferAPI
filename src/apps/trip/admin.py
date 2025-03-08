# admin.py
from django import forms
from django.contrib import admin
from django.utils import timezone
from django.db.models import Q
from .models import Trip

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        departure = cleaned_data.get('departure_time')
        arrival = cleaned_data.get('arrival_time')
        vehicle = cleaned_data.get('vehicle')

        if not all([departure, arrival, vehicle]):
            return cleaned_data

        # Валидация времени
        current_time = timezone.now()
        if departure < current_time:
            raise forms.ValidationError("Нельзя создавать поездки в прошлом")

        if arrival <= departure:
            raise forms.ValidationError("Время прибытия должно быть позже отправления")

        # Проверка доступности транспорта
        conflicts = Trip.objects.filter(vehicle=vehicle).filter(
            Q(departure_time__lt=arrival, arrival_time__gt=departure)
        ).exclude(pk=self.instance.pk if self.instance else None)

        if conflicts.exists():
            raise forms.ValidationError(
                f"Транспорт {vehicle} занят с {conflicts[0].departure_time} до {conflicts[0].arrival_time}"
            )

        return cleaned_data

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    form = TripForm
    list_display = ('origin', 'destination', 'formatted_departure', 'vehicle', 'default_ticket_price')
    list_filter = ('vehicle', 'departure_time')
    search_fields = ('origin', 'destination')

    # данные о времени в админке будут отображаться в UTC, 
    # но при редактировании или создании в UTC+10 (учитывая timezone)
    def formatted_departure(self, obj):
        return obj.departure_time.strftime('%Y-%m-%d %H:%M')
    formatted_departure.short_description = 'Departure Time'