import uuid
from io import StringIO

import pytest
from django.core.exceptions import ValidationError

from transactions.models import Transaction
from transactions.services.csv_processor import CSVProcessor


@pytest.mark.unit
class TestCSVProcessor:
    """Test CSV processing functionality"""

    def test_process_valid_csv_file(self, db, csv_file):
        """Test processing a valid CSV file"""
        processor = CSVProcessor()
        result = processor.process_file(csv_file)

        assert result['total_rows'] == 2
        assert result['successful_transactions'] == 2
        assert result['failed_rows'] == 0
        assert len(result['errors']) == 0
        assert len(result['created_transactions']) == 2

        # Verify transactions were created in database
        assert Transaction.objects.count() == 2

    def test_process_csv_with_errors(self, db, invalid_csv_file):
        """Test processing CSV file with validation errors"""
        processor = CSVProcessor()
        result = processor.process_file(invalid_csv_file)

        assert result['total_rows'] == 2
        assert result['successful_transactions'] == 0
        assert result['failed_rows'] == 2
        assert len(result['errors']) == 2

        # Check error messages contain row information
        errors = result['errors']
        assert any('Row 1' in error for error in errors)
        assert any('Row 2' in error for error in errors)

    def test_validate_uuid_field(self):
        """Test UUID validation"""
        processor = CSVProcessor()

        # Valid UUID
        valid_uuid = processor._validate_uuid('550e8400-e29b-41d4-a716-446655440000', 'test_field')
        assert isinstance(valid_uuid, uuid.UUID)

        # Invalid UUID format
        with pytest.raises(ValidationError, match="Invalid UUID format"):
            processor._validate_uuid('invalid-uuid', 'test_field')

        # Empty/None UUID
        with pytest.raises(ValidationError, match="test_field is required"):
            processor._validate_uuid(None, 'test_field')

    def test_validate_timestamp(self):
        """Test timestamp validation"""
        processor = CSVProcessor()

        # Valid ISO 8601 timestamps
        valid_timestamps = [
            '2024-01-15T10:30:00Z',
            '2024-01-15T10:30:00.123Z',
            '2024-01-15T10:30:00+02:00'
        ]

        for timestamp_str in valid_timestamps:
            result = processor._validate_timestamp(timestamp_str)
            assert result is not None

        # Invalid timestamp formats
        invalid_timestamps = [
            '2024-01-15 10:30:00',  # Space instead of T
            '2024/01/15T10:30:00Z',  # Wrong date format
            'invalid-date',
            None
        ]

        for invalid_timestamp in invalid_timestamps:
            with pytest.raises(ValidationError):
                processor._validate_timestamp(invalid_timestamp)

    def test_validate_amount(self):
        """Test amount validation"""
        processor = CSVProcessor()

        # Valid amounts
        assert processor._validate_amount('99.99') == 99.99
        assert processor._validate_amount(100) == 100.0
        assert processor._validate_amount('0.01') == 0.01

        # Invalid amounts
        with pytest.raises(ValidationError, match="amount must be positive"):
            processor._validate_amount('-10.00')

        with pytest.raises(ValidationError, match="amount must be positive"):
            processor._validate_amount('0')

        with pytest.raises(ValidationError, match="Invalid amount format"):
            processor._validate_amount('not-a-number')

        with pytest.raises(ValidationError, match="amount is required"):
            processor._validate_amount(None)

    def test_validate_currency(self):
        """Test currency validation"""
        processor = CSVProcessor()

        # Valid currencies
        for currency in ['PLN', 'EUR', 'USD']:
            assert processor._validate_currency(currency) == currency

        # Test case insensitive
        assert processor._validate_currency('pln') == 'PLN'
        assert processor._validate_currency('eur') == 'EUR'

        # Invalid currencies
        with pytest.raises(ValidationError, match="Invalid currency"):
            processor._validate_currency('GBP')

        with pytest.raises(ValidationError, match="currency is required"):
            processor._validate_currency(None)

    def test_validate_quantity(self):
        """Test quantity validation"""
        processor = CSVProcessor()

        # Valid quantities
        assert processor._validate_quantity('5') == 5
        assert processor._validate_quantity(10) == 10
        assert processor._validate_quantity('1') == 1

        # Invalid quantities
        with pytest.raises(ValidationError, match="quantity must be positive"):
            processor._validate_quantity('-1')

        with pytest.raises(ValidationError, match="quantity must be positive"):
            processor._validate_quantity('0')

        with pytest.raises(ValidationError, match="Invalid quantity format"):
            processor._validate_quantity('1.5')  # Not an integer

        with pytest.raises(ValidationError, match="Invalid quantity format"):
            processor._validate_quantity('not-a-number')

        with pytest.raises(ValidationError, match="quantity is required"):
            processor._validate_quantity(None)

    def test_missing_required_columns(self, db):
        """Test handling of missing required columns"""
        processor = CSVProcessor()

        # CSV with missing columns
        incomplete_csv_content = "transaction_id,amount\nsome-id,100.00"
        csv_file = StringIO(incomplete_csv_content)

        with pytest.raises(Exception, match="Missing required columns"):
            processor.process_file(csv_file)

    def test_empty_csv_file(self, db):
        """Test handling of empty CSV file"""
        processor = CSVProcessor()

        empty_csv = StringIO("")
        with pytest.raises(Exception):
            processor.process_file(empty_csv)

    def test_partial_success_processing(self, db):
        """Test that valid rows are processed even when some rows fail"""
        processor = CSVProcessor()

        # Mix of valid and invalid data
        mixed_csv_content = """transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
f47ac10b-58cc-4372-a567-0e02b2c3d479,2024-01-15T10:30:00Z,99.99,PLN,550e8400-e29b-41d4-a716-446655440001,6ba7b810-9dad-11d1-80b4-00c04fd430c8,2
invalid-uuid,2024-01-15T10:30:00Z,99.99,PLN,550e8400-e29b-41d4-a716-446655440001,6ba7b810-9dad-11d1-80b4-00c04fd430c8,2
f47ac10b-58cc-4372-a567-0e02b2c3d480,2024-01-15T14:22:15Z,149.50,EUR,550e8400-e29b-41d4-a716-446655440002,6ba7b810-9dad-11d1-80b4-00c04fd430c9,1"""

        csv_file = StringIO(mixed_csv_content)
        result = processor.process_file(csv_file)

        # Should have 1 success and 1 failure
        assert result['total_rows'] == 3
        assert result['successful_transactions'] == 2
        assert result['failed_rows'] == 1
        assert len(result['created_transactions']) == 2

        # Verify successful transactions were created
        assert Transaction.objects.count() == 2