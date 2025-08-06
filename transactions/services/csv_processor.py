import logging
import uuid

import pandas as pd
from django.core.exceptions import ValidationError

from ..models import Transaction

logger = logging.getLogger(__name__)


class CSVProcessor:
    REQUIRED_COLUMNS = [
        'transaction_id', 'timestamp', 'amount', 'currency',
        'customer_id', 'product_id', 'quantity'
    ]

    VALID_CURRENCIES = ['PLN', 'EUR', 'USD']

    def process_file(self, uploaded_file):
        """Process uploaded CSV file and return results"""
        try:
            df = pd.read_csv(uploaded_file)
            self._validate_columns(df)

            successful_transactions = []
            errors = []

            for index, row in df.iterrows():
                try:
                    transaction_data = self._validate_row(row, index)
                    transaction = Transaction.objects.create(**transaction_data)
                    successful_transactions.append(transaction.transaction_id)
                    logger.info(f"Created transaction: {transaction.transaction_id}")
                except ValidationError as e:
                    error_msg = f"Row {index + 1}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                except Exception as e:
                    error_msg = f"Row {index + 1}: Unexpected error - {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            return {
                'message': 'File processed successfully',
                'total_rows': len(df),
                'successful_transactions': len(successful_transactions),
                'failed_rows': len(errors),
                'errors': errors,
                'created_transactions': successful_transactions
            }

        except Exception as e:
            logger.error(f"Failed to process CSV file: {str(e)}")
            raise Exception(f"Failed to process CSV file: {str(e)}")

    def _validate_columns(self, df):
        """Validate that all required columns are present"""
        missing_columns = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")

    def _validate_row(self, row, row_index):
        """Validate and process a single row of data"""
        try:
            transaction_id = self._validate_uuid(row['transaction_id'], 'transaction_id')
            timestamp = self._validate_timestamp(row['timestamp'])
            amount = self._validate_amount(row['amount'])
            currency = self._validate_currency(row['currency'])
            customer_id = self._validate_uuid(row['customer_id'], 'customer_id')
            product_id = self._validate_uuid(row['product_id'], 'product_id')
            quantity = self._validate_quantity(row['quantity'])

            return {
                'transaction_id': transaction_id,
                'timestamp': timestamp,
                'amount': amount,
                'currency': currency,
                'customer_id': customer_id,
                'product_id': product_id,
                'quantity': quantity
            }

        except Exception as e:
            raise ValidationError(f"Invalid data: {str(e)}")

    def _validate_uuid(self, value, field_name):
        """Validate UUID format"""
        try:
            if pd.isna(value):
                raise ValidationError(f"{field_name} is required")
            return uuid.UUID(str(value))
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid UUID format for {field_name}: {value}")

    def _validate_timestamp(self, value):
        """Validate ISO 8601 timestamp"""
        try:
            if pd.isna(value):
                raise ValidationError("timestamp is required")
            return pd.to_datetime(value, format='ISO8601')
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid timestamp format: {value}")

    def _validate_amount(self, value):
        """Validate amount is a positive number"""
        try:
            if pd.isna(value):
                raise ValidationError("amount is required")
            amount = float(value)
            if amount <= 0:
                raise ValidationError(f"amount must be positive: {amount}")
            return amount
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid amount format: {value}")

    def _validate_currency(self, value):
        """Validate currency code"""
        if pd.isna(value):
            raise ValidationError("currency is required")
        currency = str(value).upper()
        if currency not in self.VALID_CURRENCIES:
            raise ValidationError(f"Invalid currency: {currency}. Must be one of {self.VALID_CURRENCIES}")
        return currency

    def _validate_quantity(self, value):
        """Validate quantity is a positive integer"""
        try:
            if pd.isna(value):
                raise ValidationError("quantity is required")
            quantity = int(value)
            if quantity <= 0:
                raise ValidationError(f"quantity must be positive: {quantity}")
            return quantity
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid quantity format: {value}")