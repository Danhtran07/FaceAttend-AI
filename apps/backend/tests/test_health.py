import os

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "backend"}


def test_settings_have_fallback_values_when_env_is_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.DATABASE_URL == "sqlite:///./faceattend.db"
    assert settings.JWT_SECRET_KEY == "development-secret-key"
