# Transaction System

A Django REST API application for processing and managing financial transactions with asynchronous CSV import capabilities using Celery.

## Features

- **Transaction Management**: CRUD operations for financial transactions
- **Asynchronous CSV Processing**: Upload and process large CSV files using Celery
- **Reports & Analytics**: Customer and product summaries, top customers/products
- **Real-time Task Status**: Track CSV processing progress
- **Comprehensive Testing**: Unit and integration tests with coverage reports
- **Dockerized**: Full Docker Compose setup with PostgreSQL, Redis, and Celery

## Tech Stack

- **Backend**: Django 5.2.2, Django REST Framework 3.15.2
- **Database**: PostgreSQL 15
- **Task Queue**: Celery 5.3.4 with Redis broker
- **Testing**: pytest, pytest-django, pytest-cov
- **Data Processing**: pandas for CSV processing
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)

### Run with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url> transaction_system
   cd transaction_system
   ```

2. **Start the services**
   ```bash
   docker compose up --build
   ```

3. **The application will be available at:**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Redis: localhost:6379
   - PostgreSQL: localhost:5432

### Local Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (create `.env` file):
   ```bash
   SECRET_KEY=your-secret-key
   DEBUG=True
   DB_NAME=transactions
   DB_USER=postgres
   DB_PASSWORD=password
   DB_HOST=localhost
   DB_PORT=5432
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Start Redis and PostgreSQL** (using Docker):
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   docker run -d -p 5432:5432 -e POSTGRES_DB=transactions -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password postgres:15
   ```

5. **Start Celery worker** (in separate terminal):
   ```bash
   celery -A transaction_system worker -l info
   ```

6. **Start Django development server**:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Transactions

#### Upload CSV File
- **POST** `/api/transactions/upload/`
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (CSV file)
- **Response**: Returns task ID for async processing
- **Status**: `202 Accepted`

**Example:**
```bash
curl -X POST -F "file=@transactions.csv" http://localhost:8000/api/transactions/upload/
```

**Response:**
```json
{
  "message": "File uploaded successfully. Processing started.",
  "task_id": "abc123-def456-ghi789",
  "status": "processing"
}
```

#### Check Task Status
- **GET** `/api/transactions/task/<task_id>/`
- **Response**: Task status and results

**Example:**
```bash
curl http://localhost:8000/api/transactions/task/abc123-def456-ghi789/
```

**Response:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "ready": true,
  "result": {
    "message": "File processed successfully",
    "total_rows": 1000,
    "successful_transactions": 995,
    "failed_rows": 5,
    "errors": ["Row 10: Invalid UUID format", ...],
    "created_transactions": ["uuid1", "uuid2", ...]
  }
}
```

#### List Transactions
- **GET** `/api/transactions/`
- **Query Parameters**: 
  - `customer_id` (optional): Filter by customer UUID
  - `product_id` (optional): Filter by product UUID
  - `page` (optional): Page number for pagination

**Example:**
```bash
curl "http://localhost:8000/api/transactions/?customer_id=123e4567-e89b-12d3-a456-426614174000&page=1"
```

#### Get Transaction Details
- **GET** `/api/transactions/<transaction_id>/`
- **Response**: Single transaction details

**Example:**
```bash
curl http://localhost:8000/api/transactions/123e4567-e89b-12d3-a456-426614174000/
```

### Reports

#### Customer Summary
- **GET** `/api/reports/customer-summary/<customer_id>/`
- **Response**: Customer transaction summary with totals

#### Product Summary
- **GET** `/api/reports/product-summary/<product_id>/`
- **Response**: Product sales summary with totals

#### Top Customers
- **GET** `/api/reports/top-customers/`
- **Query Parameters**: 
  - `limit` (optional): Number of top customers (default: 10)
- **Response**: List of top customers by total spending

#### Top Products
- **GET** `/api/reports/top-products/`
- **Query Parameters**: 
  - `limit` (optional): Number of top products (default: 10)
- **Response**: List of top products by total sales

## CSV File Format

The CSV file should contain the following columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `transaction_id` | UUID | Unique transaction identifier | `123e4567-e89b-12d3-a456-426614174000` |
| `timestamp` | ISO 8601 | Transaction timestamp | `2024-01-15T10:30:00Z` |
| `amount` | Decimal | Transaction amount (positive) | `99.99` |
| `currency` | String | Currency code (PLN, EUR, USD) | `PLN` |
| `customer_id` | UUID | Customer identifier | `456e7890-e12b-34d5-a678-901234567000` |
| `product_id` | UUID | Product identifier | `789e0123-e45f-67g8-a901-234567890000` |
| `quantity` | Integer | Product quantity (positive) | `2` |

**Example CSV:**
```csv
transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
123e4567-e89b-12d3-a456-426614174000,2024-01-15T10:30:00Z,99.99,PLN,456e7890-e12b-34d5-a678-901234567000,789e0123-e45f-67g8-a901-234567890000,2
```

## Testing

### Run All Tests
```bash
# Using pytest
pytest

# Using Django test runner
python manage.py test

# With Docker
docker compose exec web pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Specific app tests
pytest transactions/tests/
pytest reports/tests/
```

### Coverage Report
```bash
# Generate HTML coverage report
pytest --cov=transactions --cov=reports --cov=utils --cov-report=html

# View coverage in terminal
pytest --cov=transactions --cov=reports --cov=utils --cov-report=term-missing
```

Coverage reports are generated in `htmlcov/` directory.

### Test Configuration

Tests are configured in `pytest.ini`:
- Automatic Django settings detection
- Coverage for `transactions`, `reports`, and `utils` apps
- HTML and terminal coverage reports
- Custom test markers for organization

## Project Structure

```
ald/
├── transaction_system/          # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py               # Celery configuration
├── transactions/               # Transaction management app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   ├── tasks.py               # Celery tasks
│   ├── services/
│   │   ├── csv_processor.py   # CSV processing logic
│   │   └── transaction_service.py
│   └── tests/
├── reports/                   # Reports and analytics app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services/
│   │   └── report_service.py
│   └── tests/
├── utils/                     # Shared utilities
│   ├── currency.py
│   ├── logging_utils.py
│   └── middleware.py
├── logs/                      # Application logs
├── uploads/                   # Uploaded files storage
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-...` | Django secret key |
| `DEBUG` | `False` | Django debug mode |
| `DB_NAME` | `transactions` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | `password` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Celery results backend |
| `LOG_LEVEL` | `INFO` | Application log level |

## Monitoring & Logs

### Application Logs

Logs are stored in the `logs/` directory:
- `transaction_system.log` - General application logs
- `transactions.log` - Transaction-specific logs
- `reports.log` - Reports-specific logs
- `errors.log` - Error logs only
- `debug.log` - Debug logs (when DEBUG=True)

### Celery Monitoring

Monitor Celery tasks:
```bash
# View worker status
celery -A transaction_system inspect active

# View registered tasks
celery -A transaction_system inspect registered

# Monitor with Flower (optional)
pip install flower
celery -A transaction_system flower
```

## Troubleshooting

### Common Issues

1. **Celery worker not starting**
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Restart Redis
   docker compose restart redis
   ```

2. **Database connection issues**
   ```bash
   # Check PostgreSQL status
   docker compose logs db
   
   # Reset database
   docker compose down -v
   docker compose up --build
   ```

3. **CSV processing errors**
   - Check CSV format matches required columns
   - Verify UUID formats are valid
   - Check timestamp format is ISO 8601
   - Ensure amounts and quantities are positive numbers

4. **Task status returns 'PENDING'**
   - Celery worker may not be running
   - Check task ID is correct
   - Verify Redis connection