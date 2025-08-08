"""
Enhanced logging utilities for the transaction system
"""
import functools
import logging
import traceback
from django.conf import settings
from typing import Any, Dict, Optional


class TransactionSystemLogger:
    """Custom logger wrapper with enhanced functionality"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_transaction_created(self, transaction_id: str, customer_id: str,
                                amount: float, currency: str) -> None:
        """Log transaction creation with structured data"""
        self.logger.info(
            f"Transaction created - ID: {transaction_id}, "
            f"Customer: {customer_id}, Amount: {amount} {currency}"
        )

    def log_transaction_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log transaction-related errors with context"""
        self.logger.error(
            f"Transaction error: {str(error)}, Context: {context}",
            exc_info=True
        )

    def log_csv_processing(self, filename: str, rows_processed: int,
                           errors: int = 0) -> None:
        """Log CSV processing results"""
        if errors > 0:
            self.logger.warning(
                f"CSV processing completed with errors - File: {filename}, "
                f"Processed: {rows_processed}, Errors: {errors}"
            )
        else:
            self.logger.info(
                f"CSV processing completed successfully - File: {filename}, "
                f"Processed: {rows_processed} rows"
            )

    def log_report_generation(self, report_type: str, entity_id: str,
                              execution_time: float = None) -> None:
        """Log report generation"""
        message = f"Generated {report_type} report for {entity_id}"
        if execution_time:
            message += f" (execution time: {execution_time:.3f}s)"
        self.logger.info(message)

    def log_api_request(self, method: str, path: str, user: str = "anonymous",
                        status_code: int = None) -> None:
        """Log API requests"""
        message = f"API {method} {path} by {user}"
        if status_code:
            message += f" -> {status_code}"
        self.logger.info(message)

    def log_database_error(self, operation: str, error: Exception,
                           table: str = None) -> None:
        """Log database-related errors"""
        message = f"Database error during {operation}"
        if table:
            message += f" on table {table}"
        message += f": {str(error)}"
        self.logger.error(message, exc_info=True)

    def log_validation_error(self, field: str, value: Any, error_message: str) -> None:
        """Log validation errors"""
        self.logger.warning(
            f"Validation error - Field: {field}, Value: {value}, "
            f"Error: {error_message}"
        )

    def info(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Enhanced info logging with extra context"""
        self.logger.info(message, extra=extra)

    def warning(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Enhanced warning logging with extra context"""
        self.logger.warning(message, extra=extra)

    def error(self, message: str, exc_info: bool = False,
              extra: Dict[str, Any] = None) -> None:
        """Enhanced error logging with extra context"""
        self.logger.error(message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Enhanced debug logging with extra context"""
        self.logger.debug(message, extra=extra)


def get_logger(name: str) -> TransactionSystemLogger:
    """Get a custom logger instance"""
    return TransactionSystemLogger(name)


def log_exceptions(logger_name: str = None):
    """Decorator to automatically log exceptions"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise

        return wrapper

    return decorator


def log_performance(logger_name: str = None, threshold: float = 1.0):
    """Decorator to log performance metrics"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            logger = get_logger(logger_name or func.__module__)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time > threshold:
                    logger.warning(
                        f"Slow execution detected - {func.__name__}: "
                        f"{execution_time:.3f}s"
                    )
                else:
                    logger.debug(
                        f"Function {func.__name__} executed in {execution_time:.3f}s"
                    )

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Exception in {func.__name__} after {execution_time:.3f}s: {str(e)}",
                    exc_info=True
                )
                raise

        return wrapper

    return decorator


class LoggingContextManager:
    """Context manager for structured logging"""

    def __init__(self, logger: TransactionSystemLogger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation}", extra=self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        execution_time = time.time() - self.start_time

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation} successfully in {execution_time:.3f}s",
                extra=self.context
            )
        else:
            self.logger.error(
                f"Failed {self.operation} after {execution_time:.3f}s: {str(exc_val)}",
                exc_info=True,
                extra=self.context
            )


def create_logs_directory():
    """Ensure logs directory exists with proper structure"""
    from pathlib import Path
    from django.conf import settings

    logs_dir = Path(settings.BASE_DIR) / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Create subdirectories for organized logging
    (logs_dir / 'archive').mkdir(exist_ok=True)

    return logs_dir
