from django.apps import AppConfig


class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.booking'
    label = 'transfer_booking'
    verbose_name="Бронирование"

    def ready(self):
        import apps.booking.signals
