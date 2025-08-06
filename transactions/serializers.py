from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'timestamp',
            'amount',
            'currency',
            'customer_id',
            'product_id',
            'quantity',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['transaction_id', 'created_at', 'updated_at']
