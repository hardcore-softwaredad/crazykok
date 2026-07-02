# Crazy Kok Venues

A local-first web application for tracking mobile food vending opportunities in Drenthe.

## Stack

- FastAPI
- SQLAlchemy
- Alembic
- SQLite
- React + TypeScript + Vite
- Docker

## Local development

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
pytest backend/tests
```

## Docker

```bash
docker compose up --build
```
