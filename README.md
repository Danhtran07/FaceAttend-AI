# FaceAttend

## Project Overview

Face Recognition Attendance System.

## Team
- Khoa — AI Engineer
- Danh — Backend Engineer
- Tín — Frontend Engineer

## Tech Stack

Frontend:
- React
- TypeScript

Backend:
- FastAPI
- Python

Database:
- PostgreSQL

## Project Structure

This repository is a monorepo with two main services:

- `backend/` — FastAPI backend service (Danh)
- `frontend/` — Vite + React frontend (Tín)

The backend contains the API, authentication, database migrations, and health
endpoint.

## Run With Docker (recommended)

Requirements: Docker Desktop with Compose, Node.js 18 or newer, and Git.

From the repository root:

```
copy .env.example .env
docker compose up -d --build
```

The backend waits for PostgreSQL and runs the Alembic migrations automatically.
The services are available at:

- Backend: http://localhost:8000
- Backend health: http://localhost:8000/health

Run the frontend in a second terminal:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` requests to the backend, so no
frontend API URL configuration is required for local development.

JWT configuration belongs only in the backend environment. Never put
`JWT_SECRET_KEY` in frontend env files or commit the real `.env` file. For a
shared or production environment, replace the example secret with a random
value, for example:

```
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set the generated value as `JWT_SECRET_KEY` in `.env`. Keep the same secret for
all backend instances that need to validate each other's tokens. Changing it
invalidates existing login sessions.

Useful commands:

```
docker compose ps
docker compose logs -f backend
docker compose down
```

If port `8000` is already in use, change `BACKEND_PORT` in `.env`. Do not change
the internal Docker values `POSTGRES_HOST=postgres` or `DATABASE_URL`.

## Run Services Without Docker

For manual development, use a local PostgreSQL instance and set `DATABASE_URL`
accordingly. Then run:

```
cd backend
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```
cd frontend
npm install
npm run dev
```

## Current Status

MVP development with authentication, users, employees, attendance, migrations,
and health endpoints implemented.
