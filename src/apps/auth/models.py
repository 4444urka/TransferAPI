from django.db import models

# Create your models here.
class User(models.Model):
    # Пока что от балды брал максимальную минимальную длину
    phone_number = models.CharField(max_length=12, unique=True, default="null")
    password = models.CharField(max_length=30, default="null")