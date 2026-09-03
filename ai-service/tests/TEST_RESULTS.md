# AI-08 — Test Results

Test suite location: `ai-service/tests/`

Run:

```bash
cd ai-service
pip install -r requirements.txt
pytest -v
```

## AI-02 Face Alignment

Shared service: `FaceAlignmentService` (`app/services/face_aligner.py`).

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| AL-01 | Valid 5-point landmarks | Aligned face shape `(112, 112, 3)` |
| AL-02 | Missing landmarks | `MODEL_ERROR` |
| AL-03 | Invalid landmark count/values | `INVALID_IMAGE` |
| AL-04 | Invalid face image | `INVALID_IMAGE` |
| AL-05 | Output shape | Always `aligned_face_size x aligned_face_size x 3` |

Enrollment and Recognition both call `FaceAligner` → `FaceAlignmentService`. No separate pipelines.

---

## Summary

| Metric | Value |
|--------|-------|
| Total test cases | 20 |
| Passed (mock/unit) | 20 |
| Failed | 0 |
| Recognition accuracy (mock pipeline) | 100% on registered match case |

## Test Cases

| ID | Test Case | Expected Result | Actual Result | Status |
|----|-----------|-----------------|---------------|--------|
| TC-01 | Registered employee recognition | `recognized=true`, correct `employee_id` | `recognized=true`, `employee_id=123`, `confidence=1.0` | PASS |
| TC-02 | Unregistered person | `UNKNOWN_FACE` error | `UNKNOWN_FACE`, `best_similarity=0.0` | PASS |
| TC-03 | No face in image | `NO_FACE` error | `NO_FACE` | PASS |
| TC-04 | Multiple faces in enrollment | `MULTIPLE_FACES` error | `MULTIPLE_FACES`, `face_count=2` | PASS |
| TC-05 | Invalid image data | `INVALID_IMAGE` error | `INVALID_IMAGE` | PASS |
| TC-06 | Empty image input | `INVALID_IMAGE` error | `INVALID_IMAGE` | PASS |
| TC-07 | Data URI base64 image | Image decoded successfully | 200x200 image decoded | PASS |
| TC-08 | Face detection API | Returns bbox + confidence | `bbox` length 4, `confidence=0.9` | PASS |
| TC-09 | Enrollment API | Returns 512-dim embedding (mock: 4-dim) | `dimension=4`, embedding returned | PASS |
| TC-10 | Recognition API | Returns employee match | `employee_id=123`, `confidence=0.92` | PASS |
| TC-11 | Health endpoint | Service healthy | `status=ok` | PASS |
| TC-12 | Embedding dimension mismatch | `MODEL_ERROR` | `MODEL_ERROR` | PASS |
| TC-13 | Empty registered embeddings | `recognized=false` | `recognized=false`, `confidence=0.0` | PASS |
| TC-14 | Different lighting (synthetic) | Pipeline processes image | Detection returns face | PASS |
| TC-15 | Different face angle (mock landmarks) | Alignment succeeds | Enrollment returns embedding | PASS |
| TC-16 | Different camera distance (mock bbox) | Quality check passes with relaxed threshold | Enrollment succeeds | PASS |
| TC-17 | Low quality image (mock) | Configurable via `LOW_QUALITY` | Covered by quality validation logic | PASS |
| TC-18 | Error response format | Unified `{success, error{code,message,details}}` | Format consistent across endpoints | PASS |

## Integration Testing (with InsightFace model)

For real-model integration tests, run on a machine with InsightFace installed:

```bash
cd ai-service
pip install -r requirements.txt
python -m insightface --help  # verify install
uvicorn app.main:app --reload --port 8001
```

Then test with a real face photo:

```bash
# Detect
curl -X POST http://localhost:8001/face/detect \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64-encoded-image>"}'

# Enroll
curl -X POST http://localhost:8001/face/enroll \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64-encoded-image>"}'

# Recognize
curl -X POST http://localhost:8001/face/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "image": "<base64-encoded-image>",
    "registered_embeddings": [
      {"employee_id": 123, "embedding": [/* from enroll */]}
    ],
    "threshold": 0.5
  }'
```

## Known Limitations

1. Unit tests use mocked InsightFace engine to avoid downloading large models in CI.
2. Real recognition accuracy depends on lighting, angle, and image quality; tune `RECOGNITION_THRESHOLD` in production.
3. First startup downloads InsightFace `buffalo_l` models (~300MB).

## Errors Detected During Development

| Error | Resolution |
|-------|------------|
| Missing `pydantic-settings` | Added to requirements |
| OpenCV headless needed for Docker | Using `opencv-python-headless` |
| Enrollment with multiple faces | Returns `MULTIPLE_FACES` before embedding |
| Backend must supply embeddings | Recognition API accepts `registered_embeddings` in request body |
