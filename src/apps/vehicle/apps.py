from django.apps import AppConfig


class VehicleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vehicle'
    label = 'transfer_vehicle'
    verbose_name = "Транспорт"