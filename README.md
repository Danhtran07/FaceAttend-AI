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

This repository is a monorepo organized under a standard `apps/` folder:

- `apps/backend/` — FastAPI backend service (Danh)
- `apps/ai-service/` — AI model service (Khoa)
- `apps/frontend/` — Vite + React frontend (Tín)
- `database/` — database migrations and schema (if added later)

Each service contains its own app entrypoint and can run independently.

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
- AI service: http://localhost:8002
- AI service health: http://localhost:8002/health

Run the frontend in a second terminal:

```
cd apps/frontend
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
accordingly. Install backend dependencies first, then run:

```
cd apps/backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```
cd apps/frontend
npm install
npm run dev
```

To run the AI service manually, install its dependencies and start it from its
backend directory:

```bash
cd apps/ai-service/backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8001
```

The Docker setup publishes the AI service on host port `8002` by default. Set
`AI_SERVICE_HOST_PORT` in `.env` if that port is already in use.

## Current Status

AI-01 → AI-07 are implemented on `feature/khoa-ai`.

AI-08 testing report: see [`ai-service/AI_TEST_REPORT.md`](ai-service/AI_TEST_REPORT.md).

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

AI-04 Face Matching is implemented as `FaceMatchingService`:

```
Query Embedding
      ↓
Compare Candidates (from Backend)
      ↓
Cosine Similarity
      ↓
Best Match
      ↓
Threshold (FACE_MATCH_THRESHOLD)
      ↓
Employee ID / Unknown
```

- **No database access:** Backend loads embeddings from PostgreSQL and sends `candidates` to AI Service (`POST /face/match` or via `/face/recognize`).
- **Metric:** Cosine similarity on L2-normalized vectors.
- **Threshold:** configurable via `FACE_MATCH_THRESHOLD` (default `0.5`). Below threshold → `recognized=false`, `employee_id=null`, or `UNKNOWN_FACE`.
- **Output:** `{ "recognized": true/false, "employee_id": ..., "confidence": ... }`

AI-05 Recognition API:

```http
POST /face/recognize
```

**Flow**

```
Image
 ↓
Validate Image
 ↓
Face Detection
 ↓
Check Face Count (0 → NO_FACE, >1 → MULTIPLE_FACES, 1 → continue)
 ↓
Face Alignment
 ↓
Face Embedding
 ↓
Face Matching (candidates from Backend)
 ↓
Result
```

**Request**

```json
{
  "image": "<base64>",
  "candidates": [
    { "employee_id": 123, "embedding": [/* 512 floats */] }
  ],
  "threshold": 0.5
}
```

Backend loads embeddings from PostgreSQL and sends them as `candidates`. AI Service does not open a database connection.

**Recognized response**

```json
{
  "recognized": true,
  "employee_id": 123,
  "confidence": 0.92
}
```

**Unknown response** (HTTP 404)

```json
{
  "success": false,
  "error_code": "UNKNOWN_FACE",
  "message": "No matching employee",
  "details": {
    "recognized": false,
    "employee_id": null,
    "confidence": 0.31
  }
}
```

**Error cases:** `NO_FACE`, `MULTIPLE_FACES`, `UNKNOWN_FACE`, `INVALID_IMAGE`, `INVALID_EMBEDDING`, `MODEL_ERROR`

**Backend integration:** Backend authenticates the request, fetches enrolled embeddings, calls AI `/face/recognize`, then records attendance when `recognized=true`.

AI-06 Enrollment Processing:

```http
POST /face/enroll
```

**Flow**

```
Employee
   ↓
Image
   ↓
Detection
   ↓
Exactly One Face
   ↓
Alignment
   ↓
Embedding
   ↓
Return Embedding
   ↓
Backend → PostgreSQL
```

**Request**

```json
{
  "image": "<base64>"
}
```

**Success**

```json
{
  "success": true,
  "embedding": [/* float32 vector, typically 512-dim */]
}
```

**Failure**

```json
{
  "success": false,
  "error_code": "NO_FACE",
  "message": "No face detected",
  "details": null
}
```

- Uses the **same** Detector, Alignment, Embedding model, and preprocessing as Recognition.
- Exactly one face required (`0 → NO_FACE`, `>1 → MULTIPLE_FACES`).
- AI Service does **not** create/update employees or write to the database.
- **Backend responsibility:** persist the returned embedding in PostgreSQL and link it to the employee record.

AI-07 AI Error Handling:

Centralized FastAPI exception handling (`app/core/errors.py`) returns a uniform payload for `/face/enroll`, `/face/recognize`, and other AI routes:

```json
{
  "success": false,
  "error_code": "NO_FACE",
  "message": "No face detected",
  "details": null
}
```

| Error | Meaning |
| ----- | ------- |
| NO_FACE | No face detected |
| MULTIPLE_FACES | Multiple faces detected |
| UNKNOWN_FACE | No matching employee |
| INVALID_IMAGE | Invalid image |
| LOW_QUALITY | Poor face quality |
| MODEL_ERROR | Model inference error |
| INVALID_EMBEDDING | Invalid embedding |
| INVALID_REQUEST | Invalid request |

Responses never include stack traces, raw images, full embeddings, secrets, JWT, or database connection details. Server logs keep request path/method and error code for debugging without logging sensitive payloads.

The backend integration includes authentication, users, employees, attendance,
database migrations, and health endpoints.
