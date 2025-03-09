from django.db import models
from django.core.exceptions import ValidationError
import re

VEHICLE_TYPE_CHOICES = [
    ('bus', 'Автобус'),
    ('minibus', 'Микроавтобус'),
    ('car', 'Легковой автомобиль'),
    ('premium_car', 'Премиум автомобиль'),
    ('suv', 'Внедорожник'),
    ('van', 'Минивэн'),
]

def validate_license_plate(value):
    """
    Валидация автомобильных номеров.
    Поддерживаемые форматы:
    1. А111АА - автоматически добавляется регион 125
    2. А111АА 77 или А111АА77 - с указанием региона
    """
    # Приводим к верхнему регистру
    value = value.upper()
    
    # Паттерны для проверки
    # 1. Базовый формат без региона (А111АА)
    base_pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}$'
    
    # 2. Формат с регионом (А111АА 77 или А111АА77)
    with_region_pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\s?\d{2,3}$'
    
    if re.match(base_pattern, value):
        # Если номер без региона, добавляем 125
        return f"{value}125"
    elif re.match(with_region_pattern, value):
        # Если номер с регионом, убираем пробел если есть
        return value.replace(' ', '')
    else:
        raise ValidationError(
            'Неверный формат номера. Примеры: А111АА (автоматически добавится 125) '
            'или А111АА 77 (с указанием региона)'
        )

class Vehicle(models.Model):
    vehicle_type = models.CharField(
        max_length=30,
        choices=VEHICLE_TYPE_CHOICES,
        verbose_name='Тип транспорта'
    )
    license_plate = models.CharField(
        max_length=30,
        unique=True,
        validators=[validate_license_plate],
        verbose_name='Номер транспорта',
        help_text='Формат: А111АА (поставится 125 регион) или А111АА 77 (указать регион)'
    )
    total_seats = models.IntegerField(
        verbose_name='Количество мест'
    )
    is_comfort = models.BooleanField(
        default=False,
        verbose_name='Повышенный комфорт'
    )
    air_conditioning = models.BooleanField(
        default=True,
        verbose_name='Кондиционер'
    )
    allows_pets = models.BooleanField(
        default=False,
        verbose_name='Можно с животными'
    )
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Транспортное средство'
        verbose_name_plural = 'Транспортные средства'

    def clean(self):
        super().clean()
        
        # Проверка минимального и максимального количества мест (если понадобится)
        seats_limits = {
            'bus': (1, 199),
            'minibus': (1, 99),
            'car': (1, 99),
            'premium_car': (1, 99),
            'suv': (1, 99),
            'van': (1, 99),
        }
        
        min_seats, max_seats = seats_limits.get(self.vehicle_type, (1, 60))
        
        if self.total_seats < min_seats or self.total_seats > max_seats:
            raise ValidationError(
                f'Для типа {self.get_vehicle_type_display()} количество мест '
                f'должно быть от {min_seats} до {max_seats}'
            )

        # Дополнительные проверки для премиум автомобилей
        if self.vehicle_type == 'premium_car' and not self.is_comfort:
            raise ValidationError('Премиум автомобиль должен иметь повышенный уровень комфорта')

    def save(self, *args, **kwargs):
        self.clean()
        self.license_plate = validate_license_plate(self.license_plate)
        super().save(*args, **kwargs)

    def __str__(self):
        comfort = '(Комфорт)' if self.is_comfort else ''
        return f'{self.get_vehicle_type_display()} {comfort} - {self.license_plate}'
