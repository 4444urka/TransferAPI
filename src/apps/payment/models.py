from django.db import models

from apps.auth.models import User


class Payment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        default=1,
        verbose_name="Пользователь"
        )
    payment_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время операции"
        )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма")
    payment_method = models.CharField(
        max_length=30,
        verbose_name="Способ оплаты"
        )

    class Meta:
        verbose_name = "Данные об оплате"
        verbose_name_plural = "Данные об оплатах"
        ordering = ['payment_datetime']

    def __str__(self):
        return f"{self.user} - {self.payment_datetime} - {self.amount} - {self.payment_method}"