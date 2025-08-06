from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TransactionSerializer
from .services.csv_processor import CSVProcessor
from .services.transaction_service import TransactionService


class TransactionUploadView(APIView):
    """Upload CSV file with transactions"""
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith('.csv'):
            return Response(
                {'error': 'Only CSV files are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            processor = CSVProcessor()
            result = processor.process_file(file)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to process file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionListView(generics.ListAPIView):
    """List transactions with pagination and filtering"""
    serializer_class = TransactionSerializer

    def get_queryset(self):
        customer_id = self.request.query_params.get('customer_id')
        product_id = self.request.query_params.get('product_id')

        return TransactionService.filter_transactions(
            customer_id=customer_id,
            product_id=product_id
        )


class TransactionDetailView(APIView):
    """Get single transaction details"""

    def get(self, request, transaction_id):
        transaction = TransactionService.get_transaction_by_id(transaction_id)
        if not transaction:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)