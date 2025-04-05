from django.apps import AppConfig


class SeatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.seat'
    label = 'transfer_seat'
    verbose_name = "Места"
