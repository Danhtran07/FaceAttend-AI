import base64
import re
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

from app.core.errors import AIServiceError, ErrorCode

BASE64_DATA_URI_PATTERN = re.compile(r"^data:image/[\w+.-]+;base64,")


def decode_base64_image(image_data: str) -> np.ndarray:
    if not image_data or not image_data.strip():
        raise AIServiceError(
            ErrorCode.INVALID_IMAGE,
            "Image data is empty",
            status_code=400,
        )

    try:
        cleaned = BASE64_DATA_URI_PATTERN.sub("", image_data.strip())
        raw_bytes = base64.b64decode(cleaned, validate=True)
        if not raw_bytes:
            raise ValueError("Empty decoded bytes")

        pil_image = Image.open(BytesIO(raw_bytes))
        pil_image = pil_image.convert("RGB")
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except Exception as exc:
        raise AIServiceError(
            ErrorCode.INVALID_IMAGE,
            f"Failed to decode image: {exc}",
            status_code=400,
        ) from exc

    if image is None or image.size == 0:
        raise AIServiceError(
            ErrorCode.INVALID_IMAGE,
            "Decoded image is empty",
            status_code=400,
        )

    height, width = image.shape[:2]
    if height < 32 or width < 32:
        raise AIServiceError(
            ErrorCode.INVALID_IMAGE,
            "Image dimensions are too small",
            details={"width": width, "height": height},
            status_code=400,
        )

    return image


def compute_blur_variance(image: np.ndarray) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_face_size(bbox: list[float]) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)
