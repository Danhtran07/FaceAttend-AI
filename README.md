# FaceAttend AI

## Project Overview

AI-powered Face Recognition Attendance System.

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

AI:
- InsightFace
- SCRFD
- ArcFace

Database:
- PostgreSQL

## Project Structure

This repository is a monorepo with three main services:

- `backend/` — FastAPI backend service (Danh)
- `ai-service/` — AI model service (Khoa)
- `frontend/` — Vite + React frontend (Tín)
- `database/` — database migrations and schema

Each service contains a minimal skeleton and a `/health` endpoint.

## Local Development

Backend:

```
cd backend
uvicorn app.main:app --reload
```

AI service:

```
cd ai-service
uvicorn app.main:app --reload --port 8001
```

Frontend:

```
cd frontend
npm install
npm run dev
```

## Docker

From repository root:

```
docker compose up --build
```

## Current Status

Project initialization / MVP development. Health endpoints implemented; business logic to follow in later tasks.
