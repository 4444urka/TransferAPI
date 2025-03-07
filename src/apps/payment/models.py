from django.db import models

from apps.auth.models import User


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1)
    payment_datetime = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.user} - {self.payment_datetime} - {self.amount} - {self.payment_method}"