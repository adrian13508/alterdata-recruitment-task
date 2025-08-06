from transactions.models import Transaction


class TransactionService:
    """Service class for transaction business logic"""

    @staticmethod
    def get_transactions_by_customer(customer_id):
        """Get all transactions for a specific customer"""
        return Transaction.objects.filter(customer_id=customer_id)

    @staticmethod
    def get_transactions_by_product(product_id):
        """Get all transactions for a specific product"""
        return Transaction.objects.filter(product_id=product_id)

    @staticmethod
    def filter_transactions(customer_id=None, product_id=None):
        """Filter transactions by customer and/or product"""
        queryset = Transaction.objects.all()

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    @staticmethod
    def get_transaction_by_id(transaction_id):
        """Get a single transaction by ID"""
        try:
            return Transaction.objects.get(transaction_id=transaction_id)
        except Transaction.DoesNotExist:
            return None