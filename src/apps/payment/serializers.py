from rest_framework import serializers
from apps.payment.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'payment_datetime', 'amount', 'payment_method']
        read_only_fields = ['payment_datetime']