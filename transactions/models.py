import uuid

from django.db import models


class Transaction(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[
        ('PLN', 'Polish Złoty'),
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
    ])
    customer_id = models.UUIDField()
    product_id = models.UUIDField()
    quantity = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['product_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['currency']),
        ]

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency}"
