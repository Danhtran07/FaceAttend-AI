import base64

import pytest

from app.core.errors import AIServiceError, ErrorCode
from app.utils.image import decode_base64_image


def test_decode_invalid_base64():
    with pytest.raises(AIServiceError) as exc_info:
        decode_base64_image("%%%invalid%%%")
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_decode_empty_image():
    with pytest.raises(AIServiceError) as exc_info:
        decode_base64_image("")
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE


def test_decode_data_uri(sample_image_b64):
    image = decode_base64_image(f"data:image/png;base64,{sample_image_b64}")
    assert image.shape[0] == 200
    assert image.shape[1] == 200


def test_decode_too_small_image():
    tiny = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("utf-8")
    with pytest.raises(AIServiceError) as exc_info:
        decode_base64_image(tiny)
    assert exc_info.value.code == ErrorCode.INVALID_IMAGE
