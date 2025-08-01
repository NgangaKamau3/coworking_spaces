# Coworking Aggregator Platform

Enterprise-grade Django application for coworking space management with real-time IoT tracking, payments, and corporate billing.

## Features

- **User Management**: RBAC with OAuth2/JWT authentication
- **Venue Management**: Geospatial search and space management
- **Booking Engine**: Real-time availability with conflict resolution
- **Payment Integration**: Java Spring service integration with audit trails
- **IoT Integration**: Real-time occupancy tracking and verification
- **Corporate Billing**: Automated invoice generation and usage reporting
- **Reviews & Ratings**: Moderated feedback system
- **Security & Audit**: Comprehensive logging and GDPR compliance

## Architecture

```
coworking_platform/
├── apps/                   # Django applications
│   ├── authentication/     # User management & RBAC
│   ├── venues/            # Venue & space management
│   ├── bookings/          # Booking engine
│   ├── payments/          # Payment gateway integration
│   ├── billing/           # Corporate billing
│   ├── iot/               # IoT sensor integration
│   ├── reviews/           # Review system
│   └── audit/             # Audit & compliance
├── core/                  # Core utilities
│   ├── permissions/       # RBAC permissions
│   ├── middleware/        # Custom middleware
│   ├── utils/            # Utilities (encryption, etc.)
│   └── exceptions/       # Custom exceptions
├── config/               # Django configuration
└── tests/               # Comprehensive test suite
```

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL with PostGIS
- Redis
- Java Spring payment service (optional)

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd coworking_platform
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment setup**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Database setup**:
```bash
# Create PostgreSQL database with PostGIS
createdb cwspaces
psql cwspaces -c "CREATE EXTENSION postgis;"

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

4. **Create superuser**:
```bash
python manage.py createsuperuser
```

5. **Run development server**:
```bash
python manage.py runserver
```

## API Documentation

### Authentication Endpoints

- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/token/` - OAuth2 token generation
- `GET/PUT /api/v1/auth/profile/` - User profile management
- `GET/POST /api/v1/auth/companies/` - Company management

### Venue Endpoints

- `GET/POST /api/v1/venues/` - Venue listing/creation
- `GET/PUT/DELETE /api/v1/venues/{id}/` - Venue management
- `POST /api/v1/venues/search/` - Geospatial search
- `GET/POST /api/v1/venues/{id}/spaces/` - Space management

### Booking Endpoints

- `GET/POST /api/v1/bookings/` - Booking management
- `GET/PUT/DELETE /api/v1/bookings/{id}/` - Individual booking
- `POST /api/v1/bookings/availability/` - Availability check
- `POST /api/v1/bookings/{id}/confirm/` - Booking confirmation

### Payment Endpoints

- `GET /api/v1/payments/` - Payment history
- `POST /api/v1/payments/process/` - Process payment
- `POST /api/v1/payments/{id}/refund/` - Refund payment
- `POST /api/v1/payments/webhook/` - Payment webhook

### IoT Endpoints

- `GET /api/v1/iot/sensors/` - Sensor management
- `POST /api/v1/iot/webhook/` - Sensor data webhook
- `GET /api/v1/iot/spaces/{id}/occupancy/` - Real-time occupancy

## Security Features

### Authentication & Authorization
- OAuth2/JWT token-based authentication
- Role-based access control (RBAC)
- Multi-factor authentication support
- Session management

### Data Protection
- Field-level encryption for sensitive data
- GDPR compliance with data anonymization
- Audit trails for all operations
- Rate limiting and DDoS protection

### API Security
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Secure headers

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m security

# Run with coverage
pytest --cov=apps --cov-report=html
```

### Test Categories
- **Unit Tests**: Model validation, business logic
- **Integration Tests**: API endpoints, database queries
- **Security Tests**: RBAC, data encryption, vulnerability testing
- **Performance Tests**: Load testing, query optimization

## Deployment

### Production Setup

1. **Environment variables**:
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/0
```

2. **Static files**:
```bash
python manage.py collectstatic
```

3. **Database migration**:
```bash
python manage.py migrate
```

4. **Run with Gunicorn**:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Integration

### Java Spring Payment Service

The platform integrates with a Java Spring payment service through:

1. **RESTful API calls** for payment processing
2. **Webhook endpoints** for status updates
3. **Message queues** for async communication
4. **Shared database** for transaction consistency

Example integration:
```python
# Payment processing
processor = PaymentProcessor()
result = processor.process_payment(payment, gateway_type='java_spring')

# Webhook handling
@api_view(['POST'])
def payment_webhook(request):
    # Process payment status updates from Java service
    pass
```

### IoT Sensor Integration

Real-time sensor data integration via:

1. **MQTT/HTTP webhooks** for data ingestion
2. **Real-time occupancy tracking**
3. **Booking verification** through sensor data
4. **Environmental monitoring**

## Performance Optimization

### Database
- Optimized queries with select_related/prefetch_related
- Database indexing for geospatial queries
- Connection pooling
- Query caching

### Caching
- Redis caching for frequently accessed data
- API response caching
- Session caching
- Geospatial query caching

### Background Tasks
- Celery for async processing
- Automated billing cycles
- Email notifications
- Data cleanup tasks

## Monitoring & Logging

### Logging
- Structured logging with JSON format
- Audit trail logging
- Security event logging
- Performance monitoring

### Metrics
- API response times
- Database query performance
- Cache hit ratios
- Error rates

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki