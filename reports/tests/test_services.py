import uuid
from decimal import Decimal

import pytest

from reports.services.report_service import ReportService


@pytest.mark.unit
class TestReportService:
    """Test report service business logic"""

    def test_customer_summary_with_single_currency(self, db, multiple_transactions):
        """Test customer summary calculation with single currency"""
        customer_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440002')
        summary = ReportService.get_customer_summary(customer_id)

        assert summary is not None
        assert summary['customer_id'] == customer_id
        assert summary['total_transactions'] == 2
        assert summary['unique_products_count'] == 2

        # Customer 2: 75 USD * 4.0 + 25 PLN = 300 + 25 = 325 PLN
        assert float(summary['total_spent_pln']) == 325.00

    def test_customer_summary_with_mixed_currencies(self, db, multiple_transactions):
        """Test customer summary with multiple currencies"""
        customer_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440001')
        summary = ReportService.get_customer_summary(customer_id)

        assert summary is not None
        assert summary['customer_id'] == customer_id
        assert summary['total_transactions'] == 2
        assert summary['unique_products_count'] == 2

        # Customer 1: 100 PLN + 50 EUR * 4.3 = 100 + 215 = 315 PLN
        assert float(summary['total_spent_pln']) == 315.00

    def test_customer_summary_nonexistent_customer(self, db):
        """Test customer summary for non-existent customer"""
        nonexistent_customer = uuid.uuid4()
        summary = ReportService.get_customer_summary(nonexistent_customer)

        assert summary is None

    def test_product_summary_calculation(self, db, multiple_transactions):
        """Test product summary calculation"""
        product_id = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        summary = ReportService.get_product_summary(product_id)

        assert summary is not None
        assert summary['product_id'] == product_id
        assert summary['total_transactions'] == 2
        assert summary['unique_customers_count'] == 2
        assert summary['total_quantity_sold'] == 5  # 2 + 3

        # Product 1: (100 * 2) + (75 * 4.0 * 3) = 200 + 900 = 1100 PLN
        assert float(summary['total_revenue_pln']) == 1100.00

    def test_product_summary_nonexistent_product(self, db):
        """Test product summary for non-existent product"""
        nonexistent_product = uuid.uuid4()
        summary = ReportService.get_product_summary(nonexistent_product)

        assert summary is None

    def test_top_customers_by_spending(self, db, multiple_transactions):
        """Test top customers ranking"""
        top_customers = ReportService.get_top_customers_by_spending(limit=10)

        assert len(top_customers) == 2

        # Should be sorted by spending descending
        assert top_customers[0]['total_spent_pln'] >= top_customers[1]['total_spent_pln']

        # Customer 2 (325 PLN) should be first, Customer 1 (315 PLN) second
        customer_2_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440002')
        customer_1_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440001')

        assert top_customers[0]['customer_id'] == customer_2_id
        assert top_customers[1]['customer_id'] == customer_1_id

    def test_top_customers_with_limit(self, db, multiple_transactions):
        """Test top customers with limit"""
        top_customers = ReportService.get_top_customers_by_spending(limit=1)

        assert len(top_customers) == 1
        # Should return the customer with highest spending
        customer_2_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440002')
        assert top_customers[0]['customer_id'] == customer_2_id

    def test_top_products_by_revenue(self, db, multiple_transactions):
        """Test top products ranking"""
        top_products = ReportService.get_top_products_by_revenue(limit=10)

        assert len(top_products) == 2

        # Should be sorted by revenue descending
        assert top_products[0]['total_revenue_pln'] >= top_products[1]['total_revenue_pln']

        # Product 1 should have higher revenue than Product 2
        product_1_id = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        assert top_products[0]['product_id'] == product_1_id

    def test_top_products_with_limit(self, db, multiple_transactions):
        """Test top products with limit"""
        top_products = ReportService.get_top_products_by_revenue(limit=1)

        assert len(top_products) == 1
        # Should return the product with highest revenue
        product_1_id = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        assert top_products[0]['product_id'] == product_1_id

    def test_empty_database_reports(self, db):
        """Test reports with no transactions in database"""
        nonexistent_customer = uuid.uuid4()
        nonexistent_product = uuid.uuid4()

        # All should return None or empty lists
        assert ReportService.get_customer_summary(nonexistent_customer) is None
        assert ReportService.get_product_summary(nonexistent_product) is None
        assert ReportService.get_top_customers_by_spending() == []
        assert ReportService.get_top_products_by_revenue() == []

    def test_currency_conversion_precision(self, db):
        """Test that currency conversion maintains precision"""
        from transactions.models import Transaction
        from datetime import datetime

        # Create transaction with precise amounts
        customer_id = uuid.uuid4()
        product_id = uuid.uuid4()

        Transaction.objects.create(
            transaction_id=uuid.uuid4(),
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            amount=Decimal('33.33'),  # Should become 33.33 * 4.3 = 143.319 PLN
            currency='EUR',
            customer_id=customer_id,
            product_id=product_id,
            quantity=1
        )

        summary = ReportService.get_customer_summary(customer_id)

        # Should be rounded to 2 decimal places: 143.32
        assert summary['total_spent_pln'] == Decimal('143.32')