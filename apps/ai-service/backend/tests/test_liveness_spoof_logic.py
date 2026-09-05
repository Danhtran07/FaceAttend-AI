import sys
from pathlib import Path

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

    passed, count = evaluate_challenge(ChallengeType.BLINK, metrics, 19)

    assert passed is True
    assert count == 20


def test_blink_challenge_does_not_pass_without_blink_signal():
    metrics = FaceMetrics(face_detected=True, blink_score=0.2)

    passed, count = evaluate_challenge(ChallengeType.BLINK, metrics, 19)

    assert passed is False
    assert count == 0
