
from celery.result import AsyncResult
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TransactionSerializer
from .services.transaction_service import TransactionService
from .tasks import process_csv_file_async


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
            file_path = default_storage.save(f'uploads/{file.name}', file)
            task = process_csv_file_async.delay(file_path)
            
            return Response({
                'message': 'File uploaded successfully. Processing started.',
                'task_id': task.id,
                'status': 'processing'
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response(
                {'error': f'Failed to upload file: {str(e)}'},
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


class TaskStatusView(APIView):
    """Check CSV processing task status"""

    def get(self, request, task_id):
        try:
            task = AsyncResult(task_id)
            response_data = {
                'task_id': task_id,
                'status': task.status,
                'ready': task.ready()
            }
            
            if task.ready():
                if task.successful():
                    response_data['result'] = task.result
                else:
                    response_data['error'] = str(task.info)
            
            return Response(response_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get task status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )