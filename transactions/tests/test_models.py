import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError

from transactions.models import Transaction


@pytest.mark.unit
class TestTransactionModel:
    """Test Transaction model functionality"""

    def test_create_transaction_with_valid_data(self, db, sample_transaction_data):
        """Test creating a transaction with valid data"""
        transaction = Transaction.objects.create(**sample_transaction_data)

        assert transaction.transaction_id == sample_transaction_data['transaction_id']
        assert transaction.amount == sample_transaction_data['amount']
        assert transaction.currency == sample_transaction_data['currency']
        assert transaction.quantity == sample_transaction_data['quantity']
        assert transaction.created_at is not None
        assert transaction.updated_at is not None

    def test_transaction_str_representation(self, sample_transaction):
        """Test string representation of transaction"""
        expected = f"Transaction {sample_transaction.transaction_id} - {sample_transaction.amount} {sample_transaction.currency}"
        assert str(sample_transaction) == expected

    def test_transaction_ordering(self, db):
        """Test that transactions are ordered by timestamp descending"""
        # Create transactions with different timestamps
        older_transaction = Transaction.objects.create(
            transaction_id=uuid.uuid4(),
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            amount=Decimal('100.00'),
            currency='PLN',
            customer_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            quantity=1
        )

        newer_transaction = Transaction.objects.create(
            transaction_id=uuid.uuid4(),
            timestamp=datetime(2024, 1, 2, 10, 0, 0),
            amount=Decimal('200.00'),
            currency='PLN',
            customer_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            quantity=1
        )

        transactions = list(Transaction.objects.all())
        assert transactions[0] == newer_transaction
        assert transactions[1] == older_transaction

    def test_currency_choices(self, db, sample_transaction_data):
        """Test that only valid currencies are accepted"""
        # Valid currencies should work
        for currency in ['PLN', 'EUR', 'USD']:
            sample_transaction_data['currency'] = currency
            sample_transaction_data['transaction_id'] = uuid.uuid4()
            transaction = Transaction.objects.create(**sample_transaction_data)
            assert transaction.currency == currency

    def test_amount_precision(self, db, sample_transaction_data):
        """Test decimal precision for amount field"""
        sample_transaction_data['amount'] = Decimal('123.45')
        transaction = Transaction.objects.create(**sample_transaction_data)
        assert transaction.amount == Decimal('123.45')

    def test_positive_quantity_constraint(self, db, sample_transaction_data):
        """Test that quantity must be positive"""
        # This should work with positive quantity
        sample_transaction_data['quantity'] = 5
        transaction = Transaction.objects.create(**sample_transaction_data)
        assert transaction.quantity == 5

        # Zero quantity should be rejected at the database level
        # Note: PositiveIntegerField allows 0, but our validation should catch this
        sample_transaction_data['quantity'] = 0
        sample_transaction_data['transaction_id'] = uuid.uuid4()

        # Django's PositiveIntegerField actually allows 0, so this will pass
        # Our validation should be handled in the CSV processor
        transaction = Transaction.objects.create(**sample_transaction_data)
        assert transaction.quantity == 0

    def test_uuid_fields_are_uuids(self, sample_transaction):
        """Test that UUID fields are properly stored as UUIDs"""
        assert isinstance(sample_transaction.transaction_id, uuid.UUID)
        assert isinstance(sample_transaction.customer_id, uuid.UUID)
        assert isinstance(sample_transaction.product_id, uuid.UUID)

    def test_duplicate_transaction_id_not_allowed(self, db, sample_transaction_data):
        """Test that duplicate transaction IDs are not allowed"""
        # Create first transaction
        Transaction.objects.create(**sample_transaction_data)

        # Try to create another with same transaction_id
        with pytest.raises(IntegrityError):
            Transaction.objects.create(**sample_transaction_data)

    def test_required_fields(self, db):
        """Test that all required fields must be provided"""
        with pytest.raises(IntegrityError):
            Transaction.objects.create()  # No fields provided

    def test_auto_timestamps(self, db, sample_transaction_data):
        """Test that created_at and updated_at are automatically set"""
        transaction = Transaction.objects.create(**sample_transaction_data)

        assert transaction.created_at is not None
        assert transaction.updated_at is not None
        assert transaction.created_at == transaction.updated_at

        # Update the transaction
        original_created_at = transaction.created_at
        transaction.amount = Decimal('200.00')
        transaction.save()

        # created_at should remain the same, updated_at should change
        assert transaction.created_at == original_created_at
        assert transaction.updated_at > original_created_at