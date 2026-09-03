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

AI-01 Face Detection is implemented in `ai-service`.

AI-02 Face Alignment is implemented as a shared `FaceAlignmentService`:

```
Detected Face
      ↓
Facial Landmarks (InsightFace / SCRFD, 5-point)
      ↓
Alignment (ArcFace 112x112)
      ↓
Aligned Face
```

Enrollment and Recognition reuse this same alignment service. The AI service does not access the database.

AI-03 Face Embedding is implemented as `FaceEmbeddingService`:

```
Aligned Face (112x112)
      ↓
ArcFace (InsightFace buffalo_l recognition model)
      ↓
Embedding (float32, L2-normalized)
```

- **Model:** pretrained InsightFace ArcFace. No custom training. No random or fake vectors.
- **Dimension:** taken from the recognition model; buffalo_l uses **512**.
- **dtype:** `float32`.
- **Normalization:** L2 so cosine similarity is a dot product. The same aligned-face preprocessing is used for enrollment and recognition.
- **Backend responsibility:** AI Service only returns `{ "embedding": [...] }`. Backend stores the vector in the database. AI Service does not import SQLAlchemy, PostgreSQL, or backend ORM models.

