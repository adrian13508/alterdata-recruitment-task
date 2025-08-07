from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.report_service import ReportService
from .serializers import (
    CustomerSummarySerializer,
    ProductSummarySerializer,
    TopCustomerSerializer,
    TopProductSerializer
)
import logging

logger = logging.getLogger(__name__)


class CustomerSummaryView(APIView):
    """
    Get customer summary report
    GET /api/reports/customer-summary/{customer_id}/
    """

    def get(self, request, customer_id):
        try:
            # Generate customer summary
            summary = ReportService.get_customer_summary(customer_id)

            if summary is None:
                return Response(
                    {'error': f'No transactions found for customer {customer_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize and return the data
            serializer = CustomerSummarySerializer(summary)
            logger.info(f"Generated customer summary for {customer_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating customer summary for {customer_id}: {str(e)}")
            return Response(
                {'error': f'Failed to generate customer summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductSummaryView(APIView):
    """
    Get product summary report
    GET /api/reports/product-summary/{product_id}/
    """

    def get(self, request, product_id):
        try:
            # Generate product summary
            summary = ReportService.get_product_summary(product_id)

            if summary is None:
                return Response(
                    {'error': f'No transactions found for product {product_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize and return the data
            serializer = ProductSummarySerializer(summary)
            logger.info(f"Generated product summary for {product_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating product summary for {product_id}: {str(e)}")
            return Response(
                {'error': f'Failed to generate product summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopCustomersView(APIView):
    """
    Get top customers by spending (bonus feature)
    GET /api/reports/top-customers/
    """

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit > 50:  # Prevent too large requests
                limit = 50

            top_customers = ReportService.get_top_customers_by_spending(limit)
            serializer = TopCustomerSerializer(top_customers, many=True)

            return Response({
                'count': len(top_customers),
                'results': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating top customers report: {str(e)}")
            return Response(
                {'error': f'Failed to generate top customers report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopProductsView(APIView):
    """
    Get top products by revenue (bonus feature)
    GET /api/reports/top-products/
    """

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit > 50:  # Prevent too large requests
                limit = 50

            top_products = ReportService.get_top_products_by_revenue(limit)
            serializer = TopProductSerializer(top_products, many=True)

            return Response({
                'count': len(top_products),
                'results': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating top products report: {str(e)}")
            return Response(
                {'error': f'Failed to generate top products report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )