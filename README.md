# Backend API Project

Professional backend API-first architecture using FastAPI, PostgreSQL (Supabase), and repository pattern.

## Setup

1. Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
copy .env.example .env
# Edit .env with your Supabase credentials
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

- `app/core/` - Core functionality (config, database, security)
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic schemas for validation
- `app/repositories/` - Repository pattern for data access
- `app/api/v1/endpoints/` - API endpoints

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
