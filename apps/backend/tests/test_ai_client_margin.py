import json

import httpx

from app.schemas.ai import AIRecognitionCandidate
from app.services.ai_client import AIRecognitionClient


def make_client(handler):
    transport = httpx.MockTransport(handler)
    return AIRecognitionClient(
        base_url="http://ai-service:8000",
        client=httpx.Client(transport=transport),
    )


def test_recognition_sends_min_margin_when_provided():
    def handler(request):
        body = json.loads(request.content)
        assert body["min_margin"] == 0.12
        return httpx.Response(
            200,
            json={"matched": True, "employee_id": 7, "confidence": 0.94, "liveness": True},
        )

    client = make_client(handler)
    result = client.recognize(
        b"hello",
        [AIRecognitionCandidate(employee_id=7, embedding=[0.1, 0.2])],
        min_margin=0.12,
    )

    assert result.employee_id == 7
    assert result.matched is True


def test_ambiguous_match_is_normalized_as_unmatched():
    client = make_client(
        lambda request: httpx.Response(
            422,
            json={
                "matched": False,
                "confidence": 0.81,
                "liveness": True,
                "error_code": "AMBIGUOUS_MATCH",
            },
        )
    )

    result = client.recognize(b"image", [])

    assert result.matched is False
    assert result.error_code == "AMBIGUOUS_MATCH"
    assert result.liveness is True
