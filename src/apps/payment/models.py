from django.db import models


class Payment(models.Model):
    payment_datetime = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.payment_datetime} - {self.amount} - {self.payment_method}"