import json
import logging
import logging
import time
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
from django.http import JsonResponse
from django.utils import timezone
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework import status
from typing import Callable

from token_auth.models import ApiToken
from utils.logging_utils import get_logger

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log API requests and responses"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = get_logger(__name__)
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> None:
        """Log incoming requests"""
        # Store start time for performance tracking
        request._start_time = time.time()

        # Skip logging for health checks and static files
        if self._should_skip_logging(request.path):
            return

        # Log request details
        user = getattr(request, 'user', None)
        user_info = str(user) if user and hasattr(user, 'username') else 'anonymous'

        self.logger.log_api_request(
            method=request.method,
            path=request.path,
            user=user_info
        )

        # Log request body for POST/PUT/PATCH (excluding sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                if hasattr(request, 'body') and request.body:
                    body = json.loads(request.body.decode('utf-8'))
                    # Remove sensitive fields
                    sanitized_body = self._sanitize_request_body(body)
                    self.logger.debug(f"Request body: {json.dumps(sanitized_body)}")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self.logger.debug(f"Could not parse request body: {str(e)}")

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response details"""
        if self._should_skip_logging(request.path):
            return response

        # Calculate request duration
        duration = None
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time

        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = 'error'
        elif response.status_code >= 400:
            log_level = 'warning'
        else:
            log_level = 'info'

        # Prepare log message
        message = f"Response {response.status_code} for {request.method} {request.path}"
        if duration:
            message += f" in {duration:.3f}s"

        # Log with appropriate level
        getattr(self.logger, log_level)(message)

        # Log slow requests
        if duration and duration > 2.0:
            self.logger.warning(f"Slow request detected: {message}")

        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Log unhandled exceptions"""
        if self._should_skip_logging(request.path):
            return

        user = getattr(request, 'user', None)
        user_info = str(user) if user and hasattr(user, 'username') else 'anonymous'

        self.logger.error(
            f"Unhandled exception in {request.method} {request.path} "
            f"by user {user_info}: {str(exception)}",
            exc_info=True
        )

    def _should_skip_logging(self, path: str) -> bool:
        """Determine if request should be skipped from logging"""
        skip_paths = [
            '/favicon.ico',
            '/health/',
            '/static/',
            '/admin/jsi18n/',
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _sanitize_request_body(self, body: dict) -> dict:
        """Remove sensitive information from request body"""
        sensitive_fields = ['password', 'token', 'api_key', 'secret']
        sanitized = body.copy()

        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***REDACTED***'

        return sanitized


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware for centralized error handling"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.logger = get_logger(__name__)
        super().__init__(get_response)

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Handle and log exceptions centrally"""
        import traceback
        from django.http import JsonResponse
        from django.core.exceptions import ValidationError
        from django.db import IntegrityError

        # Log the exception with context
        context = {
            'method': request.method,
            'path': request.path,
            'user': str(getattr(request, 'user', 'anonymous')),
            'exception_type': type(exception).__name__,
        }

        self.logger.error(
            f"Exception occurred: {str(exception)}",
            exc_info=True,
            extra=context
        )

        # Return JSON response for API endpoints
        if request.path.startswith('/api/'):
            if isinstance(exception, ValidationError):
                return JsonResponse({
                    'error': 'Validation Error',
                    'message': str(exception),
                    'status': 400
                }, status=400)
            elif isinstance(exception, IntegrityError):
                return JsonResponse({
                    'error': 'Database Integrity Error',
                    'message': 'Data constraint violation',
                    'status': 400
                }, status=400)
            else:
                return JsonResponse({
                    'error': 'Internal Server Error',
                    'message': 'An unexpected error occurred',
                    'status': 500
                }, status=500)

        # For non-API requests, let Django handle normally
        return None


class ApiTokenAuthentication:
    """
    Simple token-based authentication middleware for API endpoints
    Token is expected as URL parameter: ?token=your_token_here
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply authentication to API endpoints
        if request.path.startswith('/api/'):
            auth_result = self.authenticate(request)
            if auth_result is not None:
                return auth_result

        response = self.get_response(request)
        return response

    def authenticate(self, request):
        """
        Authenticate request using API token from URL parameter
        Returns JsonResponse if authentication fails, None if success
        """
        # Get token from URL parameter
        token = request.GET.get('token')

        if not token:
            return JsonResponse(
                {'error': 'Token parameter required in URL.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = token.strip()

        if not token:
            return JsonResponse(
                {'error': 'Token parameter cannot be empty.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Validate token
        try:
            api_token = ApiToken.objects.get(token=token, is_active=True)

            # Update last used timestamp
            api_token.last_used_at = timezone.now()
            api_token.save(update_fields=['last_used_at'])

            logger.info(f"API request authenticated with token: {token[:8]}...")
            return None  # Success

        except ApiToken.DoesNotExist:
            logger.warning(f"Invalid API token used: {token[:8]}...")
            return JsonResponse(
                {'error': 'Invalid or inactive token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JsonResponse(
                {'error': 'Authentication failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
