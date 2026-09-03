"""AI-08 integration / architecture checks (no fabricated accuracy)."""

from fastapi.testclient import TestClient

from app.main import app
from app.services import face_engine as face_engine_module
from app.services.face_engine import get_face_engine, reset_face_engine


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-service"}


def test_face_engine_singleton_loads_once():
    reset_face_engine()
    first = get_face_engine()
    second = get_face_engine()
    assert first is second
    reset_face_engine()
    assert face_engine_module._engine is None


def test_ai_service_has_no_database_imports():
    import ast
    import pkgutil
    from pathlib import Path

    import app as app_package

    forbidden_modules = {"sqlalchemy", "psycopg", "psycopg2", "asyncpg", "backend"}
    found = []

    root = Path(app_package.__path__[0])
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in forbidden_modules:
                        found.append(f"{path.name}:import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if top in forbidden_modules:
                    found.append(f"{path.name}:from {node.module}")

    assert found == [], found


def test_enroll_and_recognize_routes_exist():
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/face/enroll" in paths
    assert "/face/recognize" in paths
    assert "/health" in paths


def test_enroll_recognize_smoke_with_stubs(client, sample_image_b64, monkeypatch):
    from app.api import face as face_api
    from app.core.schemas import FaceEnrollResponse, FaceRecognizeResponse

    monkeypatch.setattr(
        face_api.enrollment_service,
        "enroll",
        lambda image: FaceEnrollResponse(success=True, embedding=[0.1, 0.2, 0.3, 0.4]),
    )
    monkeypatch.setattr(
        face_api.recognition_service,
        "recognize",
        lambda image, candidates, threshold=None: FaceRecognizeResponse(
            recognized=True,
            employee_id=123,
            confidence=0.91,
        ),
    )

    enroll = client.post("/face/enroll", json={"image": sample_image_b64})
    assert enroll.status_code == 200
    assert enroll.json()["success"] is True
    assert isinstance(enroll.json()["embedding"], list)

    recognize = client.post(
        "/face/recognize",
        json={
            "image": sample_image_b64,
            "candidates": [{"employee_id": 123, "embedding": [0.1, 0.2, 0.3, 0.4]}],
        },
    )
    assert recognize.status_code == 200
    assert recognize.json()["recognized"] is True
