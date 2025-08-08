# Transaction System

A Django REST API application for processing and managing financial transactions with asynchronous CSV import capabilities using Celery.

## Features

- **Asynchronous CSV Processing**: Upload and process large CSV files using Celery
- **Date Range Filtering**: Generate reports for specific time periods
- **Token-based Authentication**: Secure API access with token parameters
- **Transaction Management**: CRUD operations for financial transactions
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

### Run with Docker (Recommended)

1. **Clone and start**
   ```bash
   git clone <repository-url> transaction_system
   cd transaction_system
   docker compose up --build
   ```

2. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin

## Setup Authentication

### Create Django Superuser

First, create a superuser to access the Django admin panel:

```bash
# Create superuser
docker compose exec web python manage.py createsuperuser

# Follow the prompts to set username, email, and password
```

### Create API Tokens

You can create API tokens using either the management command or Django admin panel:

**Option 1: Management Command (Recommended)**
```bash
# Create a new API token
docker compose exec web python manage.py create_token "My App Token"

# Output shows the token:
# Successfully created API token
# Name: My App Token
# Token: M8Yf5XApDxopit0Vv9UrqF2yJV_Hfukep6T7C4V290M
# Active: True

# List all tokens
docker compose exec web python manage.py list_tokens

# List only active tokens with full token values
docker compose exec web python manage.py list_tokens --active-only --show-tokens

# Create inactive token (activate later in admin)
docker compose exec web python manage.py create_token "Inactive Token" --inactive
```

**Option 2: Django Admin Panel**
1. Visit http://localhost:8000/admin
2. Login with your superuser credentials
3. Go to "Token auth" → "Api tokens"
4. Click "Add Api token"
5. Enter a name and save
6. Copy the generated token from the list

## Authentication

All API endpoints require a token parameter:

```bash
# Get your API token from the admin panel or create one programmatically
GET /api/endpoint/?token=your-api-token-here
POST /api/endpoint/?token=your-api-token-here
```

## API Endpoints

### Transactions

**Upload CSV File (Async Processing)**
```bash
POST /api/transactions/upload/?token=your-token
Content-Type: multipart/form-data
Body: file=@transactions.csv

# Returns task ID for tracking
{
  "message": "File uploaded successfully. Processing started.",
  "task_id": "abc123-def456-ghi789",
  "status": "processing"
}
```

**Check Processing Status**
```bash
GET /api/transactions/task/<task_id>/?token=your-token

# Response shows progress
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "result": {
    "total_rows": 1000,
    "successful_transactions": 995,
    "failed_rows": 5
  }
}
```

**List Transactions**
```bash
GET /api/transactions/?token=your-token
GET /api/transactions/?customer_id=uuid&token=your-token
```

### Reports with Date Filtering

All report endpoints support optional date range filtering using `start_date` and `end_date` parameters in YYYY-MM-DD format.

**Customer Summary**
```bash
# All time
GET /api/reports/customer-summary/<customer_id>/?token=your-token

# Specific date range
GET /api/reports/customer-summary/<customer_id>/?start_date=2024-01-01&end_date=2024-12-31&token=your-token

# From date onwards
GET /api/reports/customer-summary/<customer_id>/?start_date=2024-06-01&token=your-token
```

**Product Summary**
```bash
GET /api/reports/product-summary/<product_id>/?start_date=2024-01-01&end_date=2024-03-31&token=your-token
```

**Top Customers by Spending**
```bash
# Top 10 customers for specific period
GET /api/reports/top-customers/?limit=10&start_date=2024-01-01&end_date=2024-12-31&token=your-token

# Top 5 customers from March onwards
GET /api/reports/top-customers/?limit=5&start_date=2024-03-01&token=your-token
```

**Top Products by Revenue**
```bash
# Top products for Q1 2024
GET /api/reports/top-products/?limit=10&start_date=2024-01-01&end_date=2024-03-31&token=your-token
```

## CSV File Format

| Column | Type | Example |
|--------|------|---------|
| `transaction_id` | UUID | `123e4567-e89b-12d3-a456-426614174000` |
| `timestamp` | ISO 8601 | `2024-01-15T10:30:00Z` |
| `amount` | Decimal | `99.99` |
| `currency` | String | `PLN`, `EUR`, `USD` |
| `customer_id` | UUID | `456e7890-e12b-34d5-a678-901234567000` |
| `product_id` | UUID | `789e0123-e45f-67g8-a901-234567890000` |
| `quantity` | Integer | `2` |

**Example CSV:**
```csv
transaction_id,timestamp,amount,currency,customer_id,product_id,quantity
123e4567-e89b-12d3-a456-426614174000,2024-01-15T10:30:00Z,99.99,PLN,456e7890-e12b-34d5-a678-901234567000,789e0123-e45f-67g8-a901-234567890000,2
```

## Testing

```bash
# Run all tests
docker compose exec web pytest

# Run with coverage
docker compose exec web pytest --cov=transactions --cov=reports --cov=utils --cov-report=html

# Test specific apps
docker compose exec web pytest transactions/tests/
docker compose exec web pytest reports/tests/
```

## Key Features Explained

### Asynchronous Processing
- Large CSV files are processed in the background using Celery
- Returns task ID immediately for status tracking
- Prevents timeouts on large uploads

### Date Range Filtering
- Filter all reports by date range using `start_date` and `end_date`
- Supports flexible filtering (start only, end only, or both)
- Uses standard YYYY-MM-DD format

### Token Authentication
- All endpoints require a token parameter
- Simple and secure API access
- Create tokens via Django admin panel

## Project Structure

```
ald/
├── transaction_system/          # Django settings & Celery config
├── transactions/               # CSV processing & transaction management
│   ├── tasks.py               # Celery async tasks
│   └── services/
│       └── csv_processor.py   # CSV processing logic
├── reports/                   # Analytics with date filtering
│   └── services/
│       └── report_service.py  # Report generation
├── utils/                     # Shared utilities & middleware
├── token_auth/                # Token authentication
└── docker-compose.yml        # Full stack setup
```

## Troubleshooting

**CSV Processing Issues:**
- Check CSV format matches required columns
- Verify UUID formats are valid
- Ensure amounts and quantities are positive

**Authentication Issues:**
- Verify token is included in request: `?token=your-token`
- Check token is active: `docker compose exec web python manage.py list_tokens`
- Create new token: `docker compose exec web python manage.py create_token "New Token"`
- Check token in Django admin panel at http://localhost:8000/admin

**Async Task Issues:**
- Ensure Celery worker is running: `docker compose logs celery`
- Check Redis connection: `docker compose logs redis`

## Environment Setup

The application uses Docker Compose for easy setup. All services (Django, PostgreSQL, Redis, Celery) are configured and ready to run with a single command.

For production deployment, update environment variables in `docker-compose.yml` or use `.env` file for sensitive data.