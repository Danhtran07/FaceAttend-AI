from __future__ import annotations

import numpy as np
import cv2

from app.core.config import Settings, get_settings
from app.core.errors import AIServiceError, ErrorCode
from app.services.face_engine import FaceDetectionResult

# ArcFace 5-point template used by InsightFace `face_align.norm_crop` (112x112).
# Order: left eye, right eye, nose, left mouth, right mouth.
ARCFACE_SRC_112 = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)

EXPECTED_LANDMARK_COUNT = 5


class FaceAlignmentService:
    """Align a detected face to a fixed ArcFace canvas.

    Enrollment and recognition must call this same service so embeddings
    are computed from identical preprocessing.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.output_size = int(self.settings.aligned_face_size)

    def align(self, image: np.ndarray, landmarks: np.ndarray | None) -> np.ndarray:
        self._validate_face_image(image)
        points = self._validate_landmarks(landmarks, image)

        try:
            matrix = self._estimate_norm(points)
            aligned = cv2.warpAffine(
                image,
                matrix,
                (self.output_size, self.output_size),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0.0,
            )
        except AIServiceError:
            raise
        except Exception as exc:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                f"Face alignment failed: {exc}",
                status_code=500,
            ) from exc

        if aligned is None or aligned.size == 0:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Face alignment produced an empty image",
                status_code=500,
            )

        return aligned

    def align_detected_face(self, image: np.ndarray, face: FaceDetectionResult) -> np.ndarray:
        aligned = self.align(image, face.landmarks)
        face.aligned_face = aligned
        return aligned

    def _estimate_norm(self, landmarks: np.ndarray) -> np.ndarray:
        src = ARCFACE_SRC_112.copy()
        if self.output_size != 112:
            src *= self.output_size / 112.0

        matrix, inliers = cv2.estimateAffinePartial2D(
            landmarks.astype(np.float32),
            src,
            method=cv2.LMEDS,
        )
        if matrix is None:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Could not estimate alignment transform from landmarks",
                status_code=400,
            )
        if inliers is not None and int(np.sum(inliers)) < 3:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Landmarks are too unstable for alignment",
                details={"inlier_count": int(np.sum(inliers))},
                status_code=400,
            )
        return matrix

    def _validate_face_image(self, image: np.ndarray) -> None:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Face image is empty or invalid",
                status_code=400,
            )
        if image.ndim != 3 or image.shape[2] != 3:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Face image must be a BGR/RGB 3-channel array",
                details={"shape": list(image.shape)},
                status_code=400,
            )
        height, width = image.shape[:2]
        if height < 16 or width < 16:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Face image is too small to align",
                details={"width": width, "height": height},
                status_code=400,
            )

    def _validate_landmarks(
        self,
        landmarks: np.ndarray | None,
        image: np.ndarray,
    ) -> np.ndarray:
        if landmarks is None:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Facial landmarks are missing",
                status_code=400,
            )

        try:
            points = np.asarray(landmarks, dtype=np.float32)
        except Exception as exc:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Facial landmarks are invalid",
                status_code=400,
            ) from exc

        if points.size == 0:
            raise AIServiceError(
                ErrorCode.MODEL_ERROR,
                "Facial landmarks are missing",
                status_code=400,
            )

        if points.ndim != 2 or points.shape[1] != 2:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Facial landmarks must be an (N, 2) array",
                details={"shape": list(points.shape)},
                status_code=400,
            )

        if points.shape[0] != EXPECTED_LANDMARK_COUNT:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "InsightFace/SCRFD alignment requires 5 facial landmarks",
                details={
                    "expected": EXPECTED_LANDMARK_COUNT,
                    "actual": int(points.shape[0]),
                },
                status_code=400,
            )

        if not np.isfinite(points).all():
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Facial landmarks contain NaN or Inf values",
                status_code=400,
            )

        height, width = image.shape[:2]
        xs, ys = points[:, 0], points[:, 1]
        inside = (xs >= 0) & (xs < width) & (ys >= 0) & (ys < height)
        if int(np.sum(inside)) < 3:
            raise AIServiceError(
                ErrorCode.INVALID_IMAGE,
                "Facial landmarks are outside the image",
                details={"in_bounds": int(np.sum(inside))},
                status_code=400,
            )

        return points


class FaceAligner:
    """Adapter used by the shared pipeline. Delegates to FaceAlignmentService."""

    def __init__(self, engine=None, settings: Settings | None = None):
        self.service = FaceAlignmentService(settings=settings)

    def align(self, image: np.ndarray, face: FaceDetectionResult) -> np.ndarray:
        return self.service.align_detected_face(image, face)
