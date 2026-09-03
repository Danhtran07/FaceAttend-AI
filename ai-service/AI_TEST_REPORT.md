# AI Test Report

## Environment

| Item | Value |
|------|-------|
| Branch | `feature/khoa-ai` |
| Service | FaceAttend AI Service (`ai-service`) |
| Test runner | `pytest` |
| Python | 3.10 (Windows) |
| Date | 2026-09-03 |
| Real face dataset | **Not present in repository** |
| InsightFace buffalo_l in CI/local | Optional (integration test skipped when unavailable) |
| Lint tools | `ruff` / `black` / `mypy` **not configured** in this repo |

Command:

```bash
cd ai-service
python -m pytest -v
```

Result of full suite run:

```text
74 passed, 1 skipped, 0 failed in 0.99s
```

Skipped: `tests/test_face_embedding.py::test_insightface_arcface_on_aligned_face` (model not available / not downloaded).

---

## Detection

Covered in `tests/test_detection.py`, `tests/test_face_pipeline.py`.

| Case | Result |
|------|--------|
| one face | PASS |
| multiple faces | PASS (`MULTIPLE_FACES`) |
| no face | PASS (`NO_FACE`) |
| invalid image | PASS (`INVALID_IMAGE`) |

---

## Alignment

Covered in `tests/test_face_alignment.py`.

| Case | Result |
|------|--------|
| valid landmarks | PASS → shape `(112, 112, 3)` |
| invalid landmarks | PASS |
| missing landmarks | PASS |
| wrong face size | PASS |
| output shape | PASS |

---

## Embedding

Covered in `tests/test_face_embedding.py`.

| Case | Result |
|------|--------|
| valid aligned face | PASS (stub + optional InsightFace) |
| invalid input | PASS |
| empty input | PASS |
| shape | PASS `(512,)` for buffalo_l config |
| dtype | PASS `float32` |
| normalization | PASS L2 `norm ≈ 1` |

---

## Matching

Covered in `tests/test_face_matching.py`.

| Case | Result |
|------|--------|
| known employee | PASS |
| unknown employee | PASS |
| threshold pass | PASS |
| threshold fail | PASS |
| empty candidates | PASS |
| invalid embedding | PASS (`INVALID_EMBEDDING`) |
| best match | PASS |

---

## Recognition API

`POST /face/recognize` — `tests/test_recognition_api.py`, `tests/test_api.py`.

| Case | Result |
|------|--------|
| known employee | PASS |
| unknown employee | PASS (`UNKNOWN_FACE`) |
| NO_FACE | PASS |
| MULTIPLE_FACES | PASS |
| INVALID_IMAGE | PASS |
| INVALID_EMBEDDING | PASS |

---

## Enrollment API

`POST /face/enroll` — `tests/test_enrollment.py`, `tests/test_api.py`.

| Case | Result |
|------|--------|
| valid | PASS (`success=true`, embedding returned) |
| NO_FACE | PASS |
| MULTIPLE_FACES | PASS |
| INVALID_IMAGE | PASS |

---

## Error Handling

Covered in `tests/test_error_handling.py`.

Standard body verified:

```json
{
  "success": false,
  "error_code": "...",
  "message": "...",
  "details": null
}
```

Codes exercised: `NO_FACE`, `MULTIPLE_FACES`, `UNKNOWN_FACE`, `INVALID_IMAGE`, `LOW_QUALITY`, `MODEL_ERROR`, `INVALID_EMBEDDING`, `INVALID_REQUEST`.

---

## Integration / Architecture

Covered in `tests/test_integration_ai08.py`.

| Check | Result |
|-------|--------|
| `GET /health` | PASS → `{"status":"ok","service":"ai-service"}` |
| `POST /face/enroll` route | PASS (smoke with stub) |
| `POST /face/recognize` route | PASS (smoke with stub) |
| No SQLAlchemy / psycopg / asyncpg / backend ORM imports | PASS |
| FaceEngine singleton (load once) | PASS |

---

## Test Summary

| ID | Test Case | Expected | Actual | Status |
|----|-----------|----------|--------|--------|
| DET-01 | one face | 1 bbox + confidence | 1 face returned | PASS |
| DET-02 | multiple faces | `MULTIPLE_FACES` | `MULTIPLE_FACES` | PASS |
| DET-03 | no face | `NO_FACE` | `NO_FACE` | PASS |
| DET-04 | invalid image | `INVALID_IMAGE` | `INVALID_IMAGE` | PASS |
| ALN-01 | valid landmarks | `(112,112,3)` | `(112,112,3)` | PASS |
| ALN-02 | invalid landmarks | error | error | PASS |
| ALN-03 | missing landmarks | error | error | PASS |
| ALN-04 | wrong face size | `INVALID_IMAGE` | `INVALID_IMAGE` | PASS |
| ALN-05 | output shape | square canvas | square canvas | PASS |
| EMB-01 | valid aligned face | embedding vector | vector returned | PASS |
| EMB-02 | invalid/empty input | `INVALID_IMAGE` | `INVALID_IMAGE` | PASS |
| EMB-03 | shape/dtype/norm | 512 / float32 / L2=1 | matched | PASS |
| MAT-01 | known employee | recognized | recognized | PASS |
| MAT-02 | unknown employee | not recognized | not recognized | PASS |
| MAT-03 | threshold pass/fail | gate by threshold | gate by threshold | PASS |
| MAT-04 | empty / invalid / best | handled | handled | PASS |
| REC-01 | recognize known | recognized | recognized | PASS |
| REC-02 | recognize unknown | `UNKNOWN_FACE` | `UNKNOWN_FACE` | PASS |
| REC-03 | NO_FACE / MULTIPLE / INVALID_* | error codes | error codes | PASS |
| ENR-01 | enroll valid | embedding | embedding | PASS |
| ENR-02 | enroll errors | NO_FACE / MULTIPLE / INVALID_IMAGE | matched | PASS |
| INT-01 | health + singleton + no DB | architecture OK | architecture OK | PASS |
| EMB-IF | InsightFace live embedding | optional | skipped (model unavailable) | SKIP |

**Totals (pytest):** 74 passed · 0 failed · 1 skipped

---

## Accuracy

```text
NOT MEASURED
```

Reason: repository has no labeled real-face attendance dataset. Unit/integration tests use stubs and synthetic images. Fabricating Accuracy / FAR / FRR would be dishonest.

When a real dataset is available, measure:

```text
Accuracy
FAR
FRR
```

---

## Latency

```text
NOT MEASURED
```

Reason: no production-load benchmark harness or real-model latency suite in this task. Full pytest wall time for the suite was **0.99s** (mostly stubs; does not represent InsightFace inference latency).

When measuring for real:

```text
p50 / p95 enroll latency
p50 / p95 recognize latency
```

---

## Known Issues

1. InsightFace `buffalo_l` live test is skipped when the model cannot be loaded (disk/cache/environment). Production deploy must ensure model download succeeds once.
2. No real-face dataset → Accuracy / FAR / FRR / Latency remain **NOT MEASURED**.
3. `ruff` / `black` / `mypy` are not part of this repository toolchain yet.
4. C: drive disk pressure may block model downloads on some developer machines (models often cache outside `D:`).

---

## Conclusion

AI Service automated tests for Detection, Alignment, Embedding, Matching, Recognition API, Enrollment API, Error Handling, and architecture constraints (no DB access, singleton engine) are **green** on `feature/khoa-ai`.

Recognition quality metrics on real faces are **NOT MEASURED** until a labeled dataset and latency harness are added.
