# CHATUR Backend

Intelligent Adaptive Learning Platform backend built with FastAPI, SQLAlchemy 2.0 (async), SQLite (aiosqlite), and Alembic.

## Prerequisites

- Python 3.10+
- virtualenv / pip

## Quick Start

1. Install dependencies:
```bash
pip install -e .
```

2. Configure environment:
```bash
cp .env.example .env
```

3. Seed database:
```bash
python -m app.seed
```

4. Start development server:
```bash
uvicorn app.main:app --reload --port 8000
```

5. Access interactive API documentation:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
