# S PROMAX PLAST Premium ERP - Backend

PVX mahsulotlari ishlab chiqaradigan zavod uchun ERP tizimi backend API.

## Texnologiyalar

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Cache**: Redis
- **Tasks**: Celery

## O'rnatish

1. Virtual environment yaratish:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Dependencies o'rnatish:
```bash
pip install -r requirements.txt
```

3. Environment o'rnatish:
```bash
cp .env.example .env
# .env faylini tahrirlang
```

4. Database migration:
```bash
alembic upgrade head
```

5. Serverni ishga tushirish:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Server ishga tushgandan keyin:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development
```bash
# Testlar
pytest

# Code formatting
black app/

# Linting
flake8 app/
```

## Project Structure
```
erp_backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── ...
├── tests/
├── alembic/
└── ...
```