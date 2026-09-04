from __future__ import annotations

import base64

import cv2
import numpy as np


class InvalidImageError(ValueError):
    pass


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise InvalidImageError("Empty image data")
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None or frame.size == 0:
        raise InvalidImageError("Could not decode image. Provide a valid JPEG or PNG.")
    return frame


def decode_base64_image(image_b64: str) -> np.ndarray:
    payload = image_b64.split(",", 1)[-1] if "," in image_b64 else image_b64
    try:
        image_bytes = base64.b64decode(payload, validate=False)
    except Exception as exc:
        raise InvalidImageError("Invalid base64 image data") from exc
    return decode_image_bytes(image_bytes)
