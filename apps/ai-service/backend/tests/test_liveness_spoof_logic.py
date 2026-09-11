import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from liveness_engine import LivenessEngine
from challenge_evaluator import evaluate_challenge
from models import ChallengeType, FaceMetrics


def test_small_face_with_low_texture_is_not_spoof():
    engine = LivenessEngine()
    decision = engine._spoof_decision(texture_var=10.0, z_std=0.002, face_width=80, face_height=80)
    assert decision is False


def test_large_realistic_face_with_low_texture_is_still_filtered():
    engine = LivenessEngine()
    decision = engine._spoof_decision(texture_var=10.0, z_std=0.002, face_width=220, face_height=260)
    assert decision is True


def test_blink_challenge_requires_both_eyes_to_close():
    metrics = FaceMetrics(face_detected=True, blink_score=0.7)

    passed, count = evaluate_challenge(ChallengeType.BLINK, metrics, 0)

    assert passed is True
    assert count == 1


def test_blink_challenge_does_not_pass_without_blink_signal():
    metrics = FaceMetrics(face_detected=True, blink_score=0.2)

    passed, count = evaluate_challenge(ChallengeType.BLINK, metrics, 0)

    assert passed is False
    assert count == 0


def test_blink_challenge_accepts_a_normal_webcam_closure_score():
    metrics = FaceMetrics(face_detected=True, blink_score=0.25)

    passed, count = evaluate_challenge(ChallengeType.BLINK, metrics, 0)

    assert passed is True
    assert count == 1


def test_smile_challenge_accepts_a_clear_smile():
    metrics = FaceMetrics(face_detected=True, smile_score=0.6)

    passed, count = evaluate_challenge(ChallengeType.SMILE, metrics, 19)

    assert passed is True
    assert count == 20


def test_mouth_open_challenge_accepts_a_clear_mouth_open_score():
    metrics = FaceMetrics(face_detected=True, mouth_open_score=0.3)

    passed, count = evaluate_challenge(ChallengeType.MOUTH_OPEN, metrics, 19)

    assert passed is True
    assert count == 20


def test_low_light_frame_does_not_pass_liveness_challenge():
    metrics = FaceMetrics(face_detected=True, lighting_mean=18.0, is_low_light=True)

    passed, count = evaluate_challenge(ChallengeType.TURN_LEFT, metrics, 19)

    assert passed is False
    assert count == 0


def test_blink_score_uses_eye_geometry_when_blendshape_is_missing():
    landmarks = [SimpleNamespace(x=0.0, y=0.0) for _ in range(400)]
    for indices in ((33, 160, 158, 133, 153, 144), (362, 385, 387, 263, 373, 380)):
        outer, upper_a, upper_b, inner, lower_a, lower_b = indices
        landmarks[outer] = SimpleNamespace(x=0.0, y=0.0)
        landmarks[inner] = SimpleNamespace(x=1.0, y=0.0)
        landmarks[upper_a] = SimpleNamespace(x=0.5, y=0.05)
        landmarks[upper_b] = SimpleNamespace(x=0.5, y=0.05)
        landmarks[lower_a] = SimpleNamespace(x=0.5, y=-0.05)
        landmarks[lower_b] = SimpleNamespace(x=0.5, y=-0.05)

    result = SimpleNamespace(face_blendshapes=[])
    score = LivenessEngine.__new__(LivenessEngine)._compute_blink_score(result, landmarks)

    assert score >= 0.35
