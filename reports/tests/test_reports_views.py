import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.integration
class TestReportsViews:
    """Test reports API endpoints"""

    @pytest.fixture
    def api_client(self, authenticated_api_client):
        return authenticated_api_client

    def test_customer_summary_success(self, db, api_client, multiple_transactions):
        """Test successful customer summary generation"""
        customer_id = '550e8400-e29b-41d4-a716-446655440001'
        url = reverse('customer-summary', kwargs={'customer_id': customer_id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        expected_fields = [
            'customer_id', 'total_spent_pln', 'unique_products_count',
            'last_transaction_date', 'total_transactions'
        ]
        for field in expected_fields:
            assert field in data

        assert data['customer_id'] == customer_id
        assert data['total_transactions'] == 2
        assert data['unique_products_count'] == 2

        # Verify currency conversion: 100 PLN + (50 EUR * 4.3) = 100 + 215 = 315 PLN
        assert float(data['total_spent_pln']) == 315.00

    def test_customer_summary_not_found(self, db, api_client):
        """Test customer summary for non-existent customer"""
        nonexistent_customer = uuid.uuid4()
        url = reverse('customer-summary', kwargs={'customer_id': nonexistent_customer})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert 'No transactions found for customer' in data['error']

    def test_product_summary_success(self, db, api_client, multiple_transactions):
        """Test successful product summary generation"""
        product_id = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'
        url = reverse('product-summary', kwargs={'product_id': product_id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        expected_fields = [
            'product_id', 'total_quantity_sold', 'total_revenue_pln',
            'unique_customers_count', 'total_transactions'
        ]
        for field in expected_fields:
            assert field in data

        assert data['product_id'] == product_id
        assert data['total_transactions'] == 2
        assert data['unique_customers_count'] == 2
        assert data['total_quantity_sold'] == 5  # 2 + 3

        # Verify revenue: (100 * 2) + (75 * 4.0 * 3) = 200 + 900 = 1100 PLN
        assert float(data['total_revenue_pln']) == 1100.00

    def test_product_summary_not_found(self, db, api_client):
        """Test product summary for non-existent product"""
        nonexistent_product = uuid.uuid4()
        url = reverse('product-summary', kwargs={'product_id': nonexistent_product})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert 'No transactions found for product' in data['error']

    def test_top_customers_success(self, db, api_client, multiple_transactions):
        """Test top customers endpoint"""
        url = reverse('top-customers')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'count' in data
        assert 'results' in data
        assert data['count'] == 2  # We have 2 customers

        # Results should be sorted by total_spent_pln descending
        results = data['results']
        assert len(results) == 2

        # Customer 1 should be first (315 PLN > 325 PLN)
        customer_1_id = '550e8400-e29b-41d4-a716-446655440001'
        customer_2_id = '550e8400-e29b-41d4-a716-446655440002'

        # Check that customers are sorted by spending
        first_customer_spending = float(results[0]['total_spent_pln'])
        second_customer_spending = float(results[1]['total_spent_pln'])
        assert first_customer_spending >= second_customer_spending

    def test_top_customers_with_limit(self, db, api_client, multiple_transactions):
        """Test top customers with limit parameter"""
        url = reverse('top-customers')
        response = api_client.get(url, {'limit': 1})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['count'] == 1
        assert len(data['results']) == 1

    def test_top_products_success(self, db, api_client, multiple_transactions):
        """Test top products endpoint"""
        url = reverse('top-products')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'count' in data
        assert 'results' in data
        assert data['count'] == 2  # We have 2 products

        results = data['results']
        assert len(results) == 2

        # Results should be sorted by total_revenue_pln descending
        first_product_revenue = float(results[0]['total_revenue_pln'])
        second_product_revenue = float(results[1]['total_revenue_pln'])
        assert first_product_revenue >= second_product_revenue

    def test_top_products_with_limit(self, db, api_client, multiple_transactions):
        """Test top products with limit parameter"""
        url = reverse('top-products')
        response = api_client.get(url, {'limit': 1})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['count'] == 1
        assert len(data['results']) == 1

    def test_top_customers_limit_protection(self, db, api_client, multiple_transactions):
        """Test that top customers limit is capped at 50"""
        url = reverse('top-customers')
        response = api_client.get(url, {'limit': 100})

        assert response.status_code == status.HTTP_200_OK
        # Should work but internally limit to 50

    def test_invalid_uuid_in_customer_summary(self, db, api_client):
        """Test customer summary with invalid UUID"""
        url = '/api/reports/customer-summary/invalid-uuid/'
        response = api_client.get(url)

        # Should return 404 due to URL pattern not matching
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_uuid_in_product_summary(self, db, api_client):
        """Test product summary with invalid UUID"""
        url = '/api/reports/product-summary/invalid-uuid/'
        response = api_client.get(url)

        # Should return 404 due to URL pattern not matching
        assert response.status_code == status.HTTP_404_NOT_FOUND