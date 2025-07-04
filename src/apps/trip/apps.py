from django.apps import AppConfig


class TripConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.trip'
    label = 'transfer_trip'
    verbose_name = "Поездки"

    def ready(self):
        import apps.trip.signals
