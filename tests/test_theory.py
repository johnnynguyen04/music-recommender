from src.theory import (
    TrackFeatures,
    camelot_code,
    coherence_score,
    energy_continuity,
    harmonic_distance,
    tempo_compatibility,
)


def test_camelot_c_major_is_8b():
    assert camelot_code(0, 1) == "8B"
    assert camelot_code(9, 0) == "8A"  # relative minor


def test_camelot_invalid_returns_none():
    assert camelot_code(-1, 1) is None
    assert camelot_code(0, 2) is None


def test_harmonic_distance_same_code_is_zero():
    assert harmonic_distance("8B", "8B") == 0.0


def test_harmonic_distance_adjacent_on_wheel():
    # 8B and 9B are one step apart on the wheel
    assert harmonic_distance("8B", "9B") == 1.0


def test_harmonic_distance_relative_major_minor_penalty():
    # 8B (C major) -> 8A (A minor): same number, different mode
    d = harmonic_distance("8B", "8A")
    assert 0.9 < d < 1.1


def test_harmonic_distance_unknown_is_neutral():
    assert harmonic_distance(None, "8B") == 1.5


def test_tempo_compat_within_window_is_one():
    assert tempo_compatibility(120, 125) == 1.0


def test_tempo_compat_far_apart_is_zero():
    assert tempo_compatibility(100, 200) == 0.0


def test_energy_continuity_matched_is_one():
    assert energy_continuity(0.7, 0.7) == 1.0
    assert energy_continuity(0.1, 0.9) < 0.3


def test_coherence_score_smoothes_to_zero_one():
    a = TrackFeatures("a", "8B", 120.0, 0.7, 0.5, 0.6, 0.2)
    b = TrackFeatures("b", "9B", 122.0, 0.72, 0.5, 0.6, 0.2)
    s = coherence_score(a, b)
    assert 0.0 <= s <= 1.0
    assert s > 0.7  # very compatible should score high
