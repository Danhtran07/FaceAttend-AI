import base64

from fastapi import APIRouter, File, UploadFile

from app.core.schemas import (
    FaceDetectRequest,
    FaceDetectionResponse,
    FaceEnrollRequest,
    FaceEnrollResponse,
    FaceMatchRequest,
    FaceMatchResponse,
    FaceRecognizeRequest,
    FaceRecognizeResponse,
)
from app.services.enrollment import EnrollmentService
from app.services.face_matcher import FaceMatchingService
from app.services.pipeline import FacePipeline
from app.services.recognition import RecognitionService

router = APIRouter(prefix="/face", tags=["face"])

# Shared singleton stack: models load once via FaceEngine.
recognition_service = RecognitionService()
enrollment_service = EnrollmentService(
    engine=recognition_service.engine,
    detector=recognition_service.detector,
    aligner=recognition_service.aligner,
    embedder=recognition_service.embedder,
    settings=recognition_service.settings,
)
pipeline = FacePipeline(
    detector=recognition_service.detector,
    aligner=recognition_service.aligner,
    embedder=recognition_service.embedder,
    recognition=recognition_service,
)
matching_service = FaceMatchingService(settings=recognition_service.settings)


@router.post("/detect", response_model=FaceDetectionResponse)
def detect_face(payload: FaceDetectRequest) -> FaceDetectionResponse:
    """Detect faces in an image and return bounding boxes with confidence scores."""
    return pipeline.detect_faces(payload.image)


@router.post("/enroll", response_model=FaceEnrollResponse)
def enroll_face(payload: FaceEnrollRequest) -> FaceEnrollResponse:
    """Enroll a face for an employee.

    Detect → exactly one face → align → embed → return embedding.
    AI Service does not create employees or write to PostgreSQL.
    Backend stores the returned embedding.
    """
    return enrollment_service.enroll(payload.image)


@router.post("/match", response_model=FaceMatchResponse)
def match_face(payload: FaceMatchRequest) -> FaceMatchResponse:
    """Match a query embedding against Backend-supplied candidates.

    Backend loads embeddings from PostgreSQL and sends them here.
    AI Service does not access the database.
    """
    result = matching_service.match(
        payload.query_embedding,
        payload.candidates,
        threshold=payload.threshold,
    )
    return FaceMatchResponse(
        recognized=result.recognized,
        employee_id=result.employee_id,
        confidence=result.confidence,
    )


@router.post("/recognize", response_model=FaceRecognizeResponse)
def recognize_face(payload: FaceRecognizeRequest) -> FaceRecognizeResponse:
    """Full recognition for attendance check-in.

    Flow: Image → Detect → Align → Embed → Match (Backend candidates).
    One face only. Backend supplies reference embeddings; AI does not use DB.
    """
    return recognition_service.recognize(
        payload.image,
        payload.candidates,
        threshold=payload.threshold,
    )


@router.post("/detect/upload", response_model=FaceDetectionResponse)
async def detect_face_upload(file: UploadFile = File(...)) -> FaceDetectionResponse:
    content = await file.read()
    image_b64 = base64.b64encode(content).decode("utf-8")
    return pipeline.detect_faces(image_b64)


@router.post("/enroll/upload", response_model=FaceEnrollResponse)
async def enroll_face_upload(file: UploadFile = File(...)) -> FaceEnrollResponse:
    content = await file.read()
    image_b64 = base64.b64encode(content).decode("utf-8")
    return enrollment_service.enroll(image_b64)
