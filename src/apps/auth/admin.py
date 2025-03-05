from django.contrib import admin

from apps.auth.models import User
from apps.trip.models import Trip

# Register your models here.
admin.site.register(User)
admin.site.register(Trip)
