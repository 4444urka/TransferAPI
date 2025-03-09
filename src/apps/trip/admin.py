from django.contrib import admin
from django import forms
from .models import Trip

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        'origin', 
        'destination',
        'formatted_departure',
        'formatted_arrival',
        'vehicle',
        'default_ticket_price'
    )
    list_filter = ('vehicle', 'departure_time')
    search_fields = ('origin', 'destination')
    date_hierarchy = 'departure_time'
    ordering = ('-departure_time',)

    # Кастомные методы для форматирования времени (нужно для отображения времени в формате UTC) 
    # - хз надо это или нет, пока пусть будет
    def formatted_departure(self, obj):
        return obj.departure_time.strftime('%Y-%m-%d %H:%M')
    formatted_departure.short_description = 'Departure Time'

    def formatted_arrival(self, obj):
        return obj.arrival_time.strftime('%Y-%m-%d %H:%M')
    formatted_arrival.short_description = 'Arrival Time'

    # Настройка формы редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'origin', 
                'destination',
                'vehicle',
                'departure_time',
                'arrival_time',
                'default_ticket_price'
            ),
            'description': '<div class="help">Все времена указываются в часовом поясе сервера (UTC+10)</div>'
        }),
    )

    # Валидация при сохранении
    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()  # Активируем валидацию модели
            super().save_model(request, obj, form, change)
        except forms.ValidationError as e:
            form.add_error(None, e)  # Показываем ошибки в форме