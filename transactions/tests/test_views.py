import uuid
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from transactions.models import Transaction


@pytest.mark.integration
class TestTransactionViews:
    """Test transaction API endpoints"""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_upload_valid_csv_file(self, db, api_client, csv_file):
        """Test uploading a valid CSV file"""
        url = reverse('transaction-upload')
        response = api_client.post(url, {'file': csv_file}, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data['total_rows'] == 2
        assert data['successful_transactions'] == 2
        assert data['failed_rows'] == 0
        assert len(data['created_transactions']) == 2

        # Verify transactions were created
        assert Transaction.objects.count() == 2

    def test_upload_invalid_csv_file(self, db, api_client, invalid_csv_file):
        """Test uploading an invalid CSV file"""
        url = reverse('transaction-upload')
        response = api_client.post(url, {'file': invalid_csv_file}, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data['total_rows'] == 2
        assert data['successful_transactions'] == 0
        assert data['failed_rows'] == 2
        assert len(data['errors']) == 2

    def test_upload_non_csv_file(self, db, api_client, non_csv_file):
        """Test uploading a non-CSV file"""
        url = reverse('transaction-upload')
        response = api_client.post(url, {'file': non_csv_file}, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'Only CSV files are allowed' in data['error']

    def test_upload_no_file(self, db, api_client):
        """Test upload endpoint without providing a file"""
        url = reverse('transaction-upload')
        response = api_client.post(url, {}, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'No file provided' in data['error']

    def test_list_transactions(self, db, api_client, multiple_transactions):
        """Test listing all transactions"""
        url = reverse('transaction-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'results' in data
        assert len(data['results']) == 4  # We created 4 transactions

        # Check first transaction structure
        transaction = data['results'][0]
        expected_fields = [
            'transaction_id', 'timestamp', 'amount', 'currency',
            'customer_id', 'product_id', 'quantity', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            assert field in transaction

    def test_filter_transactions_by_customer(self, db, api_client, multiple_transactions):
        """Test filtering transactions by customer_id"""
        customer_id = '550e8400-e29b-41d4-a716-446655440001'
        url = reverse('transaction-list')
        response = api_client.get(url, {'customer_id': customer_id})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return 2 transactions for customer_1
        assert len(data['results']) == 2

        # All transactions should belong to the specified customer
        for transaction in data['results']:
            assert transaction['customer_id'] == customer_id

    def test_filter_transactions_by_product(self, db, api_client, multiple_transactions):
        """Test filtering transactions by product_id"""
        product_id = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'
        url = reverse('transaction-list')
        response = api_client.get(url, {'product_id': product_id})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return 2 transactions for product_1
        assert len(data['results']) == 2

        # All transactions should belong to the specified product
        for transaction in data['results']:
            assert transaction['product_id'] == product_id

    def test_filter_transactions_by_customer_and_product(self, db, api_client, multiple_transactions):
        """Test filtering transactions by both customer_id and product_id"""
        customer_id = '550e8400-e29b-41d4-a716-446655440001'
        product_id = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'

        url = reverse('transaction-list')
        response = api_client.get(url, {
            'customer_id': customer_id,
            'product_id': product_id
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return 1 transaction matching both criteria
        assert len(data['results']) == 1

        transaction = data['results'][0]
        assert transaction['customer_id'] == customer_id
        assert transaction['product_id'] == product_id

    def test_get_transaction_detail(self, db, api_client, sample_transaction):
        """Test retrieving a single transaction by ID"""
        url = reverse('transaction-detail', kwargs={'transaction_id': sample_transaction.transaction_id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['transaction_id'] == str(sample_transaction.transaction_id)
        assert data['amount'] == str(sample_transaction.amount)
        assert data['currency'] == sample_transaction.currency
        assert data['quantity'] == sample_transaction.quantity

    def test_get_nonexistent_transaction(self, db, api_client):
        """Test retrieving a transaction that doesn't exist"""
        nonexistent_id = uuid.uuid4()
        url = reverse('transaction-detail', kwargs={'transaction_id': nonexistent_id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert 'Transaction not found' in data['error']

    def test_transaction_list_pagination(self, db, api_client):
        """Test pagination in transaction list"""
        # Create more than default page size transactions
        transactions = []
        for i in range(15):
            transactions.append(Transaction(
                transaction_id=uuid.uuid4(),
                timestamp='2024-01-15T10:30:00Z',
                amount=Decimal('100.00'),
                currency='PLN',
                customer_id=uuid.uuid4(),
                product_id=uuid.uuid4(),
                quantity=1
            ))
        Transaction.objects.bulk_create(transactions)

        url = reverse('transaction-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check pagination fields
        assert 'count' in data
        assert 'next' in data
        assert 'previous' in data
        assert 'results' in data
        assert data['count'] == 15

    def test_invalid_uuid_in_detail_view(self, db, api_client):
        """Test detail view with invalid UUID format"""
        url = '/api/transactions/invalid-uuid-format/'
        response = api_client.get(url)

        # Should return 404 due to URL pattern not matching
        assert response.status_code == status.HTTP_404_NOT_FOUND