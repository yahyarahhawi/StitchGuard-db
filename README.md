# 🧵 StitchGuard API

A comprehensive quality assurance API for fabric inspection with ML integration, designed to work seamlessly with the StitchGuard iOS app.

## 🏗️ Architecture Overview

```
StitchGuard/
├── backend/                 # FastAPI application
│   ├── routers/            # API endpoints
│   ├── schemas.py          # Pydantic models
│   ├── deps.py            # Dependencies
│   └── main.py            # FastAPI app
├── db/                     # Database layer
│   ├── models.py          # SQLAlchemy models
│   ├── seed.py            # Database seeding
│   └── .env               # Database config
├── StitchGuard/           # iOS app source
└── requirements.txt       # Python dependencies
```

## ✨ Features

### 🔧 Core API Endpoints
- **Inspection Configuration**: Dynamic rule loading per product
- **Inspection Results**: Submit and track quality inspections
- **Order Management**: Create, track, and manage production orders
- **User Management**: Handle sewers and supervisors
- **Analytics**: Comprehensive statistics and reporting
- **Product Management**: Configure products and ML models

### 📊 Key Capabilities
- **Data-Driven Inspections**: Rules configured per product
- **ML Model Integration**: Support for CoreML, ONNX, PyTorch
- **Flexible Orientation System**: Any order inspection workflow
- **Real-time Statistics**: Pass rates, flaw tracking, trends
- **RESTful Design**: Clean, documented API endpoints

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Create `db/.env` file:
```bash
# For development (SQLite)
DATABASE_URL=sqlite:///./stitchguard.db

# For production (PostgreSQL)
# DATABASE_URL=postgresql://username:password@localhost:5432/stitchguard_db
```

### 3. Start the API
```bash
python start_api.py
```

The API will be available at:
- **Server**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 📱 iOS App Integration

### Core Endpoints Used by iOS App

#### 1. Get Inspection Configuration
```http
GET /api/v1/inspection/config/{product_id}
```

**Response:**
```json
{
  "product_id": 1,
  "orientations_required": ["Back", "Front"],
  "rules": [
    {
      "orientation": "Back",
      "flaw_type": "NGO",
      "rule_type": "fail_if_present",
      "stability_seconds": 3.0
    }
  ]
}
```

#### 2. Submit Inspection Results
```http
POST /api/v1/inspection/items
```

**Request:**
```json
{
  "serial_number": "ITEM-1703123456-7890",
  "order_id": 123,
  "sewer_id": 456,
  "passed": true,
  "flaws": [
    {
      "flaw_type": "NGO",
      "orientation": "Back",
      "detected_at": "2024-01-15T10:29:45Z"
    }
  ]
}
```

#### 3. Get Order Details
```http
GET /api/v1/orders/{order_id}
```

## 🗄️ Database Schema

### Core Tables
- **Users**: Sewers and supervisors
- **Products**: Item types with ML model configurations
- **Orders**: Production batches
- **Inspection Rules**: Quality criteria per product/orientation
- **Inspected Items**: Individual inspection results
- **Flaws**: Detected quality issues

### Rule Types
- `fail_if_present`: Critical failure if flaw IS detected
- `alert_if_present`: Warning if flaw IS detected  
- `fail_if_absent`: Critical failure if flaw is NOT detected
- `alert_if_absent`: Warning if flaw is NOT detected

## 🔧 API Endpoints

### Inspection Management
- `GET /api/v1/inspection/config/{product_id}` - Get inspection rules
- `POST /api/v1/inspection/items` - Submit inspection result
- `GET /api/v1/inspection/items` - List inspections (with filters)
- `GET /api/v1/inspection/items/{item_id}` - Get specific inspection

### Order Management  
- `GET /api/v1/orders` - List orders
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{order_id}` - Get order details
- `PUT /api/v1/orders/{order_id}` - Update order
- `GET /api/v1/orders/{order_id}/stats` - Order statistics

### User Management
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{user_id}` - Get user details

### Product Management
- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product
- `GET /api/v1/products/{product_id}` - Get product details

### Analytics & Reporting
- `GET /api/v1/analytics/overview` - System statistics
- `GET /api/v1/analytics/users/{user_id}/stats` - User performance
- `GET /api/v1/analytics/flaws/frequency` - Most common flaws
- `GET /api/v1/analytics/trends/daily` - Daily inspection trends

### ML Model Management
- `GET /api/v1/models` - List ML models
- `POST /api/v1/models` - Register new model
- `GET /api/v1/models/{model_id}` - Get model details

## 🧪 Sample Data

The seed script creates:
- **3 Users**: Sam (supervisor), Yahya & Jane (sewers)
- **2 Products**: Sports Bra, Cotton T-Shirt
- **2 ML Models**: OrientationClassifier, YOLOv8
- **2 Orders**: With realistic inspection data
- **40+ Inspected Items**: With pass/fail results
- **Inspection Rules**: Product-specific quality criteria

## 🛠️ Development

### Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Testing
```bash
pytest tests/
```

### Production Deployment
```bash
# Using Gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Docker
docker build -t stitchguard-api .
docker run -p 8000:8000 stitchguard-api
```

## 🔐 Security Considerations

### For Production:
1. **Environment Variables**: Use proper secrets management
2. **CORS**: Restrict allowed origins to your iOS app domain
3. **Authentication**: Implement JWT or OAuth2
4. **Database**: Use PostgreSQL with proper connection pooling
5. **HTTPS**: Enable SSL/TLS encryption
6. **Rate Limiting**: Prevent API abuse

### Example Production Settings:
```python
# In backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-ios-app-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## 📈 Performance Optimization

### Database
- **Indexing**: Add indexes on frequently queried fields
- **Connection Pooling**: Configure SQLAlchemy pool settings
- **Query Optimization**: Use eager loading for relationships

### Caching
- **Redis**: Cache inspection configurations
- **Response Caching**: Cache analytics endpoints
- **Static Files**: Use CDN for ML model files

### Monitoring
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Track API response times and error rates
- **Health Checks**: Monitor database and external services

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the database schema in `db/models.py`
3. Examine sample data in `db/seed.py`
4. Open an issue on GitHub

# Trigger redeploy Thu Jun 26 14:24:12 EDT 2025
# Force Railway Redeploy - Thu Jun 26 15:12:51 EDT 2025

# StitchGuard Database

This is the backend database and API for the StitchGuard quality inspection system.

## Recent Changes

### Removed Order Seeding
- **Removed all order creation from `seed.py`** - Orders are no longer automatically created during database seeding
- **Deleted `create_test_assignments.sql`** - Manual order assignment script removed
- **Focus on Bra Inspection Only** - Only bra inspection products and models are seeded

### What Gets Seeded Now
- ✅ Users (Sam Wood, Yahya Rahhawi, Jane Smith)
- ✅ ML Models for bra inspection only (orientation classifier + YOLO detection)
- ✅ Bra product configuration
- ✅ Inspection rules for bra products
- ❌ No orders (create manually via API)
- ❌ No T-shirt or other products

### Model Installation Fix
- Updated model URLs to use `bundle://` prefix for bundled models
- This should resolve model installation issues by using locally bundled models instead of non-existent CDN URLs

## Usage

### 1. Database Setup
```bash
cd StitchGuard-db
python -m pip install -r requirements.txt
python db/seed.py
```

### 2. Start API Server
```bash
cd StitchGuard-db
python start_api.py
```

### 3. Create Orders Manually
Orders should now be created manually through:
- API endpoints (POST `/api/v1/orders`)
- Admin interface (if implemented)
- Direct database insertion

## API Endpoints
- `GET /api/v1/products` - List available products (bra only)
- `GET /api/v1/products/{id}/models` - Get models for a product
- `POST /api/v1/orders` - Create new orders
- `GET /api/v1/orders/assigned-to/{user_id}` - Get assigned orders

## Notes
- The system now focuses exclusively on bra inspection workflows
- Models are bundled locally to avoid download/installation issues
- Orders must be created manually or through separate management tools
