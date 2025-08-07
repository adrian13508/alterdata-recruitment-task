from decimal import Decimal

from django.db.models import Sum, Max

from transactions.models import Transaction
from utils.currency import convert_to_pln


class ReportService:
    """Service for generating customer and product reports"""

    @staticmethod
    def get_customer_summary(customer_id):
        """
        Generate customer summary report

        Returns:
            dict: Customer summary with total_spent_pln, unique_products_count, last_transaction_date
        """
        # Get all transactions for the customer
        customer_transactions = Transaction.objects.filter(customer_id=customer_id)

        if not customer_transactions.exists():
            return None

        # Calculate total spent in PLN (convert from different currencies)
        total_spent_pln = Decimal('0.00')

        for transaction in customer_transactions:
            amount_in_pln = convert_to_pln(transaction.amount, transaction.currency)
            total_spent_pln += amount_in_pln

        # Count unique products purchased
        unique_products = customer_transactions.values('product_id').distinct().count()

        # Get last transaction date
        last_transaction = customer_transactions.aggregate(
            last_date=Max('timestamp')
        )['last_date']

        return {
            'customer_id': customer_id,
            'total_spent_pln': round(total_spent_pln, 2),
            'unique_products_count': unique_products,
            'last_transaction_date': last_transaction,
            'total_transactions': customer_transactions.count()
        }

    @staticmethod
    def get_product_summary(product_id):
        """
        Generate product summary report

        Returns:
            dict: Product summary with total_quantity_sold, total_revenue_pln, unique_customers_count
        """
        # Get all transactions for the product
        product_transactions = Transaction.objects.filter(product_id=product_id)

        if not product_transactions.exists():
            return None

        # Calculate total quantity sold
        total_quantity = product_transactions.aggregate(
            total=Sum('quantity')
        )['total'] or 0

        # Calculate total revenue in PLN (convert from different currencies)
        total_revenue_pln = Decimal('0.00')

        for transaction in product_transactions:
            transaction_revenue = transaction.amount * transaction.quantity
            revenue_in_pln = convert_to_pln(transaction_revenue, transaction.currency)
            total_revenue_pln += revenue_in_pln

        # Count unique customers who bought this product
        unique_customers = product_transactions.values('customer_id').distinct().count()

        # Get additional stats
        total_transactions = product_transactions.count()

        return {
            'product_id': product_id,
            'total_quantity_sold': total_quantity,
            'total_revenue_pln': round(total_revenue_pln, 2),
            'unique_customers_count': unique_customers,
            'total_transactions': total_transactions
        }

    @staticmethod
    def get_top_customers_by_spending(limit=10):
        """Get top customers by total spending (bonus feature)"""
        customer_totals = []

        # Get all unique customers
        customers = Transaction.objects.values('customer_id').distinct()

        for customer in customers:
            customer_id = customer['customer_id']
            summary = ReportService.get_customer_summary(customer_id)
            if summary:
                customer_totals.append(summary)

        # Sort by total spent (descending)
        return sorted(customer_totals, key=lambda x: x['total_spent_pln'], reverse=True)[:limit]

    @staticmethod
    def get_top_products_by_revenue(limit=10):
        """Get top products by total revenue (bonus feature)"""
        product_totals = []

        # Get all unique products
        products = Transaction.objects.values('product_id').distinct()

        for product in products:
            product_id = product['product_id']
            summary = ReportService.get_product_summary(product_id)
            if summary:
                product_totals.append(summary)

        # Sort by total revenue (descending)
        return sorted(product_totals, key=lambda x: x['total_revenue_pln'], reverse=True)[:limit]