import logging
from celery import shared_task
from django.core.files.storage import default_storage
from .services.csv_processor import CSVProcessor

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_csv_file_async(self, file_path):
    """
    Asynchronous task to process CSV file
    """
    try:
        logger.info(f"Starting async CSV processing for file: {file_path}")
        
        with default_storage.open(file_path, 'rb') as file:
            processor = CSVProcessor()
            result = processor.process_file(file)
            
        logger.info(f"Completed async CSV processing for file: {file_path}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing CSV file {file_path}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)