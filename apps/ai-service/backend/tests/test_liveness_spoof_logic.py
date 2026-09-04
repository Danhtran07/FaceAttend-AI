import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from liveness_engine import LivenessEngine


def test_small_face_with_low_texture_is_not_spoof():
    engine = LivenessEngine()
    decision = engine._spoof_decision(texture_var=10.0, z_std=0.002, face_width=80, face_height=80)
    assert decision is False


def test_large_realistic_face_with_low_texture_is_still_filtered():
    engine = LivenessEngine()
    decision = engine._spoof_decision(texture_var=10.0, z_std=0.002, face_width=220, face_height=260)
    assert decision is True
