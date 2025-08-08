from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime, date

from django.db.models import Sum, Max

from transactions.models import Transaction
from utils.currency import convert_to_pln
from utils.logging_utils import get_logger, LoggingContextManager, log_exceptions, log_performance


class ReportService:
    """Service for generating customer and product reports"""

    @staticmethod
    @log_exceptions('reports.services.report_service')
    @log_performance('reports.services.report_service', threshold=2.0)
    def get_customer_summary(customer_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Generate customer summary report

        Args:
            customer_id: UUID of the customer
            start_date: Optional start date for filtering transactions
            end_date: Optional end date for filtering transactions

        Returns:
            dict: Customer summary with total_spent_pln, unique_products_count, last_transaction_date
            None: If customer not found or has no transactions
        """
        logger = get_logger(__name__)
        
        with LoggingContextManager(logger, f"customer summary generation",
                                   customer_id=customer_id):
            try:
                # Get all transactions for the customer with optional date filtering
                customer_transactions = Transaction.objects.filter(customer_id=customer_id)
                
                # Apply date range filtering if provided
                if start_date:
                    customer_transactions = customer_transactions.filter(timestamp__date__gte=start_date)
                if end_date:
                    customer_transactions = customer_transactions.filter(timestamp__date__lte=end_date)

                if not customer_transactions.exists():
                    logger.warning(f"No transactions found for customer {customer_id}")
                    return None

                transaction_count = customer_transactions.count()
                logger.info(f"Processing {transaction_count} transactions for customer {customer_id}")

                # Calculate total spent in PLN (convert from different currencies)
                total_spent_pln = Decimal('0.00')
                conversion_errors = 0

                for transaction in customer_transactions:
                    try:
                        amount_in_pln = convert_to_pln(transaction.amount, transaction.currency)
                        total_spent_pln += amount_in_pln
                    except Exception as e:
                        conversion_errors += 1
                        logger.error(
                            f"Currency conversion failed for transaction {transaction.id}: {str(e)}",
                            exc_info=True
                        )

                if conversion_errors > 0:
                    logger.warning(
                        f"Currency conversion errors: {conversion_errors} out of {transaction_count} transactions"
                    )

                # Count unique products purchased
                unique_products = customer_transactions.values('product_id').distinct().count()

                # Get last transaction date
                last_transaction = customer_transactions.aggregate(
                    last_date=Max('timestamp')
                )['last_date']

                summary = {
                    'customer_id': customer_id,  # Keep as UUID for service layer
                    'total_spent_pln': round(total_spent_pln, 2),  # Keep as Decimal for service layer
                    'unique_products_count': unique_products,
                    'last_transaction_date': last_transaction,  # Keep as datetime for service layer
                    'total_transactions': transaction_count
                }

                logger.log_report_generation(
                    "customer summary",
                    customer_id
                )

                return summary

            except Exception as e:
                logger.error(
                    f"Error generating customer summary for {customer_id}: {str(e)}",
                    exc_info=True
                )
                raise

    @staticmethod
    @log_exceptions('reports.services.report_service')
    @log_performance('reports.services.report_service', threshold=2.0)
    def get_product_summary(product_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Generate product summary report

        Args:
            product_id: UUID of the product
            start_date: Optional start date for filtering transactions
            end_date: Optional end date for filtering transactions

        Returns:
            dict: Product summary with total_quantity_sold, total_revenue_pln, unique_customers_count
            None: If product not found or has no transactions
        """
        logger = get_logger(__name__)
        
        with LoggingContextManager(logger, f"product summary generation",
                                   product_id=product_id):
            try:
                # Get all transactions for the product with optional date filtering
                product_transactions = Transaction.objects.filter(product_id=product_id)
                
                # Apply date range filtering if provided
                if start_date:
                    product_transactions = product_transactions.filter(timestamp__date__gte=start_date)
                if end_date:
                    product_transactions = product_transactions.filter(timestamp__date__lte=end_date)

                if not product_transactions.exists():
                    logger.warning(f"No transactions found for product {product_id}")
                    return None

                transaction_count = product_transactions.count()
                logger.info(f"Processing {transaction_count} transactions for product {product_id}")

                # Calculate total quantity sold
                total_quantity = product_transactions.aggregate(
                    total=Sum('quantity')
                )['total'] or 0

                # Calculate total revenue in PLN (convert from different currencies)
                total_revenue_pln = Decimal('0.00')
                conversion_errors = 0

                for transaction in product_transactions:
                    try:
                        transaction_revenue = transaction.amount * transaction.quantity
                        revenue_in_pln = convert_to_pln(transaction_revenue, transaction.currency)
                        total_revenue_pln += revenue_in_pln
                    except Exception as e:
                        conversion_errors += 1
                        logger.error(
                            f"Revenue calculation failed for transaction {transaction.id}: {str(e)}",
                            exc_info=True
                        )

                if conversion_errors > 0:
                    logger.warning(
                        f"Revenue calculation errors: {conversion_errors} out of {transaction_count} transactions"
                    )

                # Count unique customers who bought this product
                unique_customers = product_transactions.values('customer_id').distinct().count()

                summary = {
                    'product_id': product_id,  # Keep as UUID for service layer
                    'total_quantity_sold': total_quantity,
                    'total_revenue_pln': round(total_revenue_pln, 2),  # Keep as Decimal for service layer
                    'unique_customers_count': unique_customers,
                    'total_transactions': transaction_count
                }

                logger.log_report_generation(
                    "product summary",
                    product_id
                )

                return summary

            except Exception as e:
                logger.error(
                    f"Error generating product summary for {product_id}: {str(e)}",
                    exc_info=True
                )
                raise

    @staticmethod
    @log_exceptions('reports.services.report_service')
    @log_performance('reports.services.report_service', threshold=5.0)
    def get_top_customers_by_spending(limit: int = 10, start_date: Optional[date] = None, end_date: Optional[date] = None) -> list:
        """Get top customers by total spending with optional date range filtering"""
        logger = get_logger(__name__)
        
        with LoggingContextManager(logger, f"top customers report generation", limit=limit):
            try:
                customer_totals = []

                # Get all unique customer IDs properly
                unique_customer_ids = list(set(Transaction.objects.values_list('customer_id', flat=True)))
                total_customers = len(unique_customer_ids)

                logger.info(f"Processing {total_customers} unique customers for top spending report")

                processed = 0
                errors = 0

                for customer_id in unique_customer_ids:
                    try:
                        summary = ReportService.get_customer_summary(customer_id, start_date, end_date)
                        if summary:
                            customer_totals.append(summary)
                        processed += 1

                        # Log progress for large datasets
                        if processed % 100 == 0:
                            logger.info(f"Processed {processed}/{total_customers} customers")

                    except Exception as e:
                        errors += 1
                        logger.error(
                            f"Error processing customer {customer_id}: {str(e)}"
                        )

                if errors > 0:
                    logger.warning(f"Completed with {errors} errors out of {total_customers} customers")

                # Sort by total spent (descending)
                result = sorted(customer_totals, key=lambda x: x['total_spent_pln'], reverse=True)[:limit]

                logger.info(f"Generated top {len(result)} customers report successfully")
                return result

            except Exception as e:
                logger.error(f"Error generating top customers report: {str(e)}", exc_info=True)
                raise

    @staticmethod
    @log_exceptions('reports.services.report_service')
    @log_performance('reports.services.report_service', threshold=5.0)
    def get_top_products_by_revenue(limit: int = 10, start_date: Optional[date] = None, end_date: Optional[date] = None) -> list:
        """Get top products by total revenue with optional date range filtering"""
        logger = get_logger(__name__)
        
        with LoggingContextManager(logger, f"top products report generation", limit=limit):
            try:
                product_totals = []

                # Get all unique product IDs properly
                unique_product_ids = list(set(Transaction.objects.values_list('product_id', flat=True)))
                total_products = len(unique_product_ids)

                logger.info(f"Processing {total_products} unique products for top revenue report")

                processed = 0
                errors = 0

                for product_id in unique_product_ids:
                    try:
                        summary = ReportService.get_product_summary(product_id, start_date, end_date)
                        if summary:
                            product_totals.append(summary)
                        processed += 1

                        # Log progress for large datasets
                        if processed % 100 == 0:
                            logger.info(f"Processed {processed}/{total_products} products")

                    except Exception as e:
                        errors += 1
                        logger.error(
                            f"Error processing product {product_id}: {str(e)}"
                        )

                if errors > 0:
                    logger.warning(f"Completed with {errors} errors out of {total_products} products")

                # Sort by total revenue (descending)
                result = sorted(product_totals, key=lambda x: x['total_revenue_pln'], reverse=True)[:limit]

                logger.info(f"Generated top {len(result)} products report successfully")
                return result

            except Exception as e:
                logger.error(f"Error generating top products report: {str(e)}", exc_info=True)
                raise