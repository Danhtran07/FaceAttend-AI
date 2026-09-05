import base64
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.ai import (
    AIRecognitionCandidate,
    AIRecognitionResult,
    LivenessSessionResponse,
)


class AIServiceUnavailableError(Exception):
    pass


class AIServiceTimeoutError(Exception):
    pass


class AIServiceResponseError(Exception):
    pass


class AIRecognitionClient:
    def __init__(
        self,
        base_url: str = settings.AI_SERVICE_URL,
        timeout_seconds: float = settings.AI_SERVICE_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        self._endpoint = f"{base_url.rstrip('/')}/face/recognize"
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def recognize(
        self,
        face_image: bytes,
        candidates: list[AIRecognitionCandidate],
        threshold: float = 0.5,
        liveness_session_id: str | None = None,
    ) -> AIRecognitionResult:
        payload = {
            "image": base64.b64encode(face_image).decode("ascii"),
            "candidates": [candidate.model_dump() for candidate in candidates],
            "threshold": threshold,
            "liveness_session_id": liveness_session_id,
        }

        try:
            response = self._client.post(self._endpoint, json=payload)
        except httpx.TimeoutException as exc:
            raise AIServiceTimeoutError("AI Service request timed out") from exc
        except httpx.RequestError as exc:
            raise AIServiceUnavailableError("AI Service is unavailable") from exc

        try:
            response_data = response.json()
        except (ValueError, TypeError) as exc:
            raise AIServiceResponseError("AI Service returned invalid JSON") from exc

        if not isinstance(response_data, dict):
            raise AIServiceResponseError("AI Service returned an invalid response")

        error_code = response_data.get("error_code")
        if error_code in {"NO_FACE", "MULTIPLE_FACES", "FACE_NOT_RECOGNIZED", "LIVENESS_FAILED"}:
            response_data = {
                **response_data,
                "matched": False,
                "liveness": response_data.get("liveness", False),
            }

        try:
            return AIRecognitionResult.model_validate(response_data)
        except (TypeError, ValueError) as exc:
            raise AIServiceResponseError("AI Service returned an invalid recognition result") from exc

    def create_liveness_session(self) -> LivenessSessionResponse:
        try:
            response = self._client.post(f"{self._endpoint.rsplit('/face/', 1)[0]}/session/create")
        except httpx.TimeoutException as exc:
            raise AIServiceTimeoutError("AI Service request timed out") from exc
        except httpx.RequestError as exc:
            raise AIServiceUnavailableError("AI Service is unavailable") from exc

        try:
            return LivenessSessionResponse.model_validate(response.json())
        except (TypeError, ValueError) as exc:
            raise AIServiceResponseError("AI Service returned an invalid liveness session") from exc

    def __enter__(self) -> "AIRecognitionClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()