from rest_framework import serializers


class CustomerSummarySerializer(serializers.Serializer):
    """Serializer for customer summary report"""
    customer_id = serializers.UUIDField()
    total_spent_pln = serializers.DecimalField(max_digits=12, decimal_places=2)
    unique_products_count = serializers.IntegerField()
    last_transaction_date = serializers.DateTimeField()
    total_transactions = serializers.IntegerField()


class ProductSummarySerializer(serializers.Serializer):
    """Serializer for product summary report"""
    product_id = serializers.UUIDField()
    total_quantity_sold = serializers.IntegerField()
    total_revenue_pln = serializers.DecimalField(max_digits=12, decimal_places=2)
    unique_customers_count = serializers.IntegerField()
    total_transactions = serializers.IntegerField()


class TopCustomerSerializer(serializers.Serializer):
    """Serializer for top customers list (bonus feature)"""
    customer_id = serializers.UUIDField()
    total_spent_pln = serializers.DecimalField(max_digits=12, decimal_places=2)
    unique_products_count = serializers.IntegerField()
    last_transaction_date = serializers.DateTimeField()
    total_transactions = serializers.IntegerField()


class TopProductSerializer(serializers.Serializer):
    """Serializer for top products list (bonus feature)"""
    product_id = serializers.UUIDField()
    total_quantity_sold = serializers.IntegerField()
    total_revenue_pln = serializers.DecimalField(max_digits=12, decimal_places=2)
    unique_customers_count = serializers.IntegerField()
    total_transactions = serializers.IntegerField()