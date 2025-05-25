from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from apps.vehicle.models import Vehicle, validate_license_plate


class VehicleAdminForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        license_plate = cleaned_data.get('license_plate')

        if license_plate:
            try:
                # Нормализуем номер
                normalized_plate = validate_license_plate(license_plate)
                
                # Проверяем существование
                existing = Vehicle.objects.filter(
                    license_plate=normalized_plate
                ).exclude(pk=self.instance.pk).first()
                
                if existing:
                    created = existing.created_at.strftime("%d.%m.%Y") if hasattr(existing, 'created_at') else 'ранее'
                    self.add_error('license_plate', 
                        f'Транспорт с номером {normalized_plate} уже существует в базе '
                        f'(тип: {existing.get_vehicle_type_display()}, добавлен {created})'
                    )
                else:
                    cleaned_data['license_plate'] = normalized_plate
                    
            except ValidationError as e:
                self.add_error('license_plate', str(e))

        return cleaned_data


class VehicleAdmin(admin.ModelAdmin):
    form = VehicleAdminForm
    list_display = ('id', 'vehicle_type', 'license_plate', 'total_seats', 'is_comfort', 'air_conditioning', 'allows_pets')
    list_filter = ('vehicle_type', 'is_comfort', 'air_conditioning', 'allows_pets')
    search_fields = ('license_plate',)
    fieldsets = (
        (None, {'fields': ('vehicle_type', 'license_plate', 'total_seats')}),
        ('Дополнительно', {'fields': ('is_comfort', 'air_conditioning', 'allows_pets')}),
    )


admin.site.register(Vehicle, VehicleAdmin)
