# Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker (for PostgreSQL and Redis)
- Spotify Premium account

## Setup

### 1. Start Infrastructure Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379

### 2. Set Up Python Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Then edit `.env` with your Spotify OAuth credentials:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Copy Client ID and Client Secret to `.env`
4. Set Redirect URI to `http://localhost:8000/callback`

### 5. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 6. Access Documentation

- API docs: `http://localhost:8000/docs` (Swagger UI)
- Root endpoint: `http://localhost:8000/`

## Next Steps

1. Visit `/auth/login` to authenticate with Spotify
2. After authentication, you'll be redirected to the dashboard
3. Use the listening event API to track plays

## Development

### Run Tests

```bash
pytest
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```
