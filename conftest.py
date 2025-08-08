
import uuid
from datetime import datetime
from decimal import Decimal

import pytest
import django
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

# Configure Django settings before any model imports
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transaction_system.settings')
django.setup()

# Now we can safely import models
from transactions.models import Transaction
from token_auth.models import ApiToken


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return {
        'transaction_id': uuid.uuid4(),
        'timestamp': datetime(2024, 1, 15, 10, 30, 0),
        'amount': Decimal('99.99'),
        'currency': 'PLN',
        'customer_id': uuid.uuid4(),
        'product_id': uuid.uuid4(),
        'quantity': 2
    }


@pytest.fixture
def sample_transaction(db, sample_transaction_data):
    """Create a sample transaction in the database"""
    return Transaction.objects.create(**sample_transaction_data)


@pytest.fixture
def multiple_transactions(db):
    """Create multiple transactions for testing reports"""
    customer_1 = uuid.UUID('550e8400-e29b-41d4-a716-446655440001')
    customer_2 = uuid.UUID('550e8400-e29b-41d4-a716-446655440002')
    product_1 = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    product_2 = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c9')

    transactions = [
        # Customer 1 transactions
        Transaction(
            transaction_id=uuid.uuid4(),
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            amount=Decimal('100.00'),
            currency='PLN',
            customer_id=customer_1,
            product_id=product_1,
            quantity=2
        ),
        Transaction(
            transaction_id=uuid.uuid4(),
            timestamp=datetime(2024, 1, 16, 14, 22, 15),
            amount=Decimal('50.00'),
            currency='EUR',  # 50 * 4.3 = 215 PLN
            customer_id=customer_1,
            product_id=product_2,
            quantity=1
        ),
        # Customer 2 transactions
        Transaction(
            transaction_id=uuid.uuid4(),
            timestamp=datetime(2024, 1, 17, 9, 15, 30),
            amount=Decimal('75.00'),
            currency='USD',  # 75 * 4.0 = 300 PLN
            customer_id=customer_2,
            product_id=product_1,
            quantity=3
        ),
        Transaction(
            transaction_id=uuid.uuid4(),
            timestamp=datetime(2024, 1, 18, 16, 45, 22),
            amount=Decimal('25.00'),
            currency='PLN',
            customer_id=customer_2,
            product_id=product_2,
            quantity=1
        ),
    ]

    return Transaction.objects.bulk_create(transactions)


@pytest.fixture
def valid_csv_content():
    """Valid CSV content for testing uploads"""
    return """transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
f47ac10b-58cc-4372-a567-0e02b2c3d479,2024-01-15T10:30:00Z,99.99,PLN,550e8400-e29b-41d4-a716-446655440001,6ba7b810-9dad-11d1-80b4-00c04fd430c8,2
f47ac10b-58cc-4372-a567-0e02b2c3d480,2024-01-15T14:22:15Z,149.50,EUR,550e8400-e29b-41d4-a716-446655440002,6ba7b810-9dad-11d1-80b4-00c04fd430c9,1"""


@pytest.fixture
def invalid_csv_content():
    """Invalid CSV content for testing error handling"""
    return """transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
invalid-uuid,2024-01-15T10:30:00Z,99.99,PLN,550e8400-e29b-41d4-a716-446655440001,6ba7b810-9dad-11d1-80b4-00c04fd430c8,2
f47ac10b-58cc-4372-a567-0e02b2c3d480,invalid-date,149.50,EUR,550e8400-e29b-41d4-a716-446655440002,6ba7b810-9dad-11d1-80b4-00c04fd430c9,-1"""


@pytest.fixture
def csv_file(valid_csv_content):
    """Create a CSV file for upload testing"""
    file_content = valid_csv_content.encode('utf-8')
    return SimpleUploadedFile(
        "test_transactions.csv",
        file_content,
        content_type="text/csv"
    )


@pytest.fixture
def invalid_csv_file(invalid_csv_content):
    """Create an invalid CSV file for error testing"""
    file_content = invalid_csv_content.encode('utf-8')
    return SimpleUploadedFile(
        "test_invalid_transactions.csv",
        file_content,
        content_type="text/csv"
    )


@pytest.fixture
def non_csv_file():
    """Create a non-CSV file for testing file type validation"""
    return SimpleUploadedFile(
        "test.txt",
        b"not a csv file",
        content_type="text/plain"
    )


@pytest.fixture
def api_token(db):
    """Create an API token for testing"""
    return ApiToken.objects.create(
        name="Test Token",
        is_active=True
    )


@pytest.fixture
def authenticated_api_client(api_token):
    """API client with authentication token"""
    from rest_framework.test import APIClient
    
    class AuthenticatedAPIClient(APIClient):
        def __init__(self, token, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.token = token
            
        def get(self, path, data=None, **extra):
            if data is None:
                data = {}
            data['token'] = self.token
            return super().get(path, data, **extra)
            
        def post(self, path, data=None, **extra):
            if '?' in path:
                path += f'&token={self.token}'
            else:
                path += f'?token={self.token}'
            return super().post(path, data, **extra)
            
        def put(self, path, data=None, **extra):
            if '?' in path:
                path += f'&token={self.token}'
            else:
                path += f'?token={self.token}'
            return super().put(path, data, **extra)
            
        def patch(self, path, data=None, **extra):
            if '?' in path:
                path += f'&token={self.token}'
            else:
                path += f'?token={self.token}'
            return super().patch(path, data, **extra)
            
        def delete(self, path, data=None, **extra):
            if '?' in path:
                path += f'&token={self.token}'
            else:
                path += f'?token={self.token}'
            return super().delete(path, data, **extra)
    
    return AuthenticatedAPIClient(api_token.token)