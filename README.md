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

This repository is a monorepo organized under a standard `apps/` folder:

- `apps/backend/` — FastAPI backend service (Danh)
- `apps/ai-service/` — AI model service (Khoa)
- `apps/frontend/` — Vite + React frontend (Tín)
- `database/` — database migrations and schema (if added later)

Each service contains its own app entrypoint and can run independently.

## Local Development

Backend:

```
cd apps/backend
uvicorn app.main:app --reload
```

AI service:

```
cd apps/ai-service
uvicorn app.main:app --reload --port 8001
```

Frontend:

```
cd apps/frontend
npm install
npm run dev
```

## Docker

From repository root:

```
docker compose up --build
```

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

