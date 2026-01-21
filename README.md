# S PROMAX PLAST ERP Backend

Modern, to'liq funksional ERP tizimi backend qismi FastAPI bilan qurilgan.

## 🚀 Modullar

### ✅ 1. Authentication & Users
- JWT autentifikatsiya
- Role-based access control (RBAC)
- Permission management
- User CRUD

### ✅ 2. Warehouse Management
- Supplier management
- Raw material inventory
- Warehouse receipts
- Stock tracking
- Material requests

### ✅ 3. Production Management
- Production lines
- Machine management
- Finished products
- Shift management
- Production records & output
- Defect tracking
- Quality control

### ✅ 4. Sales & CRM
- Customer management
- Order processing
- Payment tracking
- Stock reservation
- Delivery management

### ✅ 5. Finance & Accounting
- Transaction categories
- Income/Expense tracking
- P&L Reports
- Cash Flow Reports
- Balance Sheet
- Automatic transaction creation

### ✅ 6. Human Resources
- Department management
- Employee records
- Attendance tracking
- Salary payments
- Leave requests & approval

### ✅ 7. Maintenance Management
- Maintenance requests
- Work logging
- Spare parts inventory
- Maintenance scheduling
- Machine status integration

### ✅ 8. Analytics & Reporting
- Dashboard overview
- Sales analytics
- Production analytics
- Finance analytics
- HR analytics
- Inventory analytics
- Maintenance analytics
- KPI metrics
- Quick stats & alerts

## 📊 Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Migration**: Alembic
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic v2
- **Password Hashing**: Passlib with bcrypt

## 🗄️ Database

- **Total Tables**: 37
- **Total Endpoints**: 150+
- **Modules**: 9

## 🚀 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+

### Setup

1. Clone repository
```bash
git clone <repository-url>
cd erp_backend
```

2. Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create .env file
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run migrations
```bash
alembic upgrade head
```

6. Seed data
```bash
python scripts/seed_initial_data.py
python scripts/seed_warehouse_data.py
python scripts/seed_production_data.py
python scripts/seed_sales_data.py
python scripts/seed_finance_data.py
python scripts/seed_hr_data.py
python scripts/seed_maintenance_data.py
```

7. Run server
```bash
uvicorn app.main:app --reload
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Default Credentials
```
Email: admin@spromax.uz
Password: Admin123!
```

## 🏗️ Project Structure
```
erp_backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── warehouse.py
│   │       ├── production.py
│   │       ├── sales.py
│   │       ├── finance.py
│   │       ├── hr.py
│   │       ├── maintenance.py
│   │       └── analytics.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── constants.py
│   │   └── exceptions.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── dependencies.py
│   ├── database.py
│   └── main.py
├── alembic/
├── scripts/
├── .env
├── requirements.txt
└── README.md
```

## 🧪 Testing

Access Swagger UI at http://localhost:8000/docs for interactive API testing.

## 📈 Features

- ✅ Clean Architecture
- ✅ Repository Pattern
- ✅ Service Layer
- ✅ JWT Authentication
- ✅ Role-Based Access Control
- ✅ Complex Business Logic
- ✅ Cross-Module Integration
- ✅ Comprehensive Analytics
- ✅ RESTful API Design
- ✅ Data Validation
- ✅ Error Handling
- ✅ Database Migrations

## 🐳 Docker bilan ishga tushirish

### Prerequisites
- Docker 20.10+
- Docker Compose V2

### Quick Start

1. **Start services**
```bash
chmod +x start.sh
./start.sh
```

Yoki qo'lda:
```bash
# Build
docker compose build

# Start
docker compose up -d

# Migrations
docker compose exec api alembic upgrade head

# Seed data
make seed
```

2. **Access API**
- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

3. **View logs**
```bash
make logs
# or
docker compose logs -f api
```

4. **Stop services**
```bash
./stop.sh
# or
docker compose down
```

### Useful Commands
```bash
# Show running containers
make ps
docker compose ps

# Access API container shell
make shell
docker compose exec api bash

# Access database
make db-shell
docker compose exec db psql -U promax_user -d promax_erp

# Restart services
make restart
docker compose restart

# View all logs
docker compose logs -f

# Clean everything (including volumes)
make clean
docker compose down -v
```

### Development
```bash
# Rebuild without cache
docker compose build --no-cache

# Run in foreground (see logs)
docker compose up

# Restart single service
docker compose restart api
```

## 👨‍💻 Author

**Asliddin** - Python Backend Developer & Programming Instructor

## 📝 License

Proprietary - S PROMAX PLAST

---

**Status**: Production Ready ✨
**Version**: 1.0.0
**Completion**: 100%