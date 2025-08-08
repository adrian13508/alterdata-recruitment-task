import logging
from datetime import datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.services.report_service import ReportService
from .serializers import CustomerSummarySerializer, ProductSummarySerializer

logger = logging.getLogger(__name__)


def parse_date_parameter(date_str):
    """Parse date string in YYYY-MM-DD format"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {date_str}")


class CustomerSummaryView(APIView):
    """
    Get customer summary report
    GET /api/reports/customer-summary/{customer_id}/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """

    def get(self, request, customer_id):
        try:
            # Parse date parameters
            start_date = parse_date_parameter(request.query_params.get('start_date'))
            end_date = parse_date_parameter(request.query_params.get('end_date'))

            # Generate customer summary with optional date filtering
            summary = ReportService.get_customer_summary(str(customer_id), start_date, end_date)

            if summary is None:
                date_filter = ""
                if start_date or end_date:
                    date_filter = f" (filtered from {start_date or 'beginning'} to {end_date or 'end'})"
                return Response(
                    {'error': f'No transactions found for customer {customer_id}{date_filter}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize and return the data
            serializer = CustomerSummarySerializer(summary)
            logger.info(f"Generated customer summary for {customer_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generating customer summary for {customer_id}: {str(e)}")
            return Response(
                {'error': f'Failed to generate customer summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductSummaryView(APIView):
    """
    Get product summary report
    GET /api/reports/product-summary/{product_id}/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """

    def get(self, request, product_id):
        try:
            # Parse date parameters
            start_date = parse_date_parameter(request.query_params.get('start_date'))
            end_date = parse_date_parameter(request.query_params.get('end_date'))

            # Generate product summary with optional date filtering
            summary = ReportService.get_product_summary(str(product_id), start_date, end_date)

            if summary is None:
                date_filter = ""
                if start_date or end_date:
                    date_filter = f" (filtered from {start_date or 'beginning'} to {end_date or 'end'})"
                return Response(
                    {'error': f'No transactions found for product {product_id}{date_filter}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize and return the data
            serializer = ProductSummarySerializer(summary)
            logger.info(f"Generated product summary for {product_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generating product summary for {product_id}: {str(e)}")
            return Response(
                {'error': f'Failed to generate product summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopCustomersView(APIView):
    """
    Get top customers by spending
    GET /api/reports/top-customers/?limit=10&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """

    def get(self, request):
        try:
            # Get limit from query parameters, default to 10
            limit = int(request.query_params.get('limit', 10))

            # Validate limit
            if limit <= 0 or limit > 100:
                return Response(
                    {'error': 'Limit must be between 1 and 100'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse date parameters
            start_date = parse_date_parameter(request.query_params.get('start_date'))
            end_date = parse_date_parameter(request.query_params.get('end_date'))

            # Generate top customers report with optional date filtering
            top_customers = ReportService.get_top_customers_by_spending(limit, start_date, end_date)

            # Convert data for JSON serialization
            results = []
            for customer in top_customers:
                result = customer.copy()
                result['customer_id'] = str(result['customer_id'])
                result['total_spent_pln'] = str(result['total_spent_pln'])
                if result['last_transaction_date']:
                    result['last_transaction_date'] = result['last_transaction_date'].isoformat()
                results.append(result)

            # Return paginated response format
            response_data = {
                'count': len(results),
                'results': results
            }
            logger.info(f"Generated top {len(top_customers)} customers report")
            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generating top customers report: {str(e)}")
            return Response(
                {'error': f'Failed to generate top customers report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopProductsView(APIView):
    """
    Get top products by revenue
    GET /api/reports/top-products/?limit=10&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """

    def get(self, request):
        try:
            # Get limit from query parameters, default to 10
            limit = int(request.query_params.get('limit', 10))

            # Validate limit
            if limit <= 0 or limit > 100:
                return Response(
                    {'error': 'Limit must be between 1 and 100'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse date parameters
            start_date = parse_date_parameter(request.query_params.get('start_date'))
            end_date = parse_date_parameter(request.query_params.get('end_date'))

            # Generate top products report with optional date filtering
            top_products = ReportService.get_top_products_by_revenue(limit, start_date, end_date)

            # Convert data for JSON serialization
            results = []
            for product in top_products:
                result = product.copy()
                result['product_id'] = str(result['product_id'])
                result['total_revenue_pln'] = str(result['total_revenue_pln'])
                results.append(result)

            # Return paginated response format
            response_data = {
                'count': len(results),
                'results': results
            }
            logger.info(f"Generated top {len(top_products)} products report")
            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generating top products report: {str(e)}")
            return Response(
                {'error': f'Failed to generate top products report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
