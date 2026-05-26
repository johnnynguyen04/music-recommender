"""music theory features used by the hybrid model.

three pieces:
  1. Camelot wheel mapping from (key, mode) -> Camelot code (e.g. "8B")
  2. pairwise harmonic distance on the wheel
  3. tempo and energy compatibility heuristics dj's use for mixing

the wheel is the standard tool for harmonic mixing; adjacent positions share
many notes, so cuts between them sound smooth. our hybrid uses the harmonic
distance to penalize jarring transitions inside a recommended playlist tail.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# spotify api convention: key is pitch class 0..11 (C=0, C#=1, ..., B=11),
# mode is 1 for major, 0 for minor.

# (pitch_class, mode) -> camelot code. mode==1 means major (B), mode==0 minor (A).
# numbers come from the standard wheel layout.
_CAMELOT: dict[tuple[int, int], str] = {
    (0, 1): "8B",   (9, 0): "8A",     # C major / A minor
    (7, 1): "9B",   (4, 0): "9A",     # G major / E minor
    (2, 1): "10B",  (11, 0): "10A",   # D major / B minor
    (9, 1): "11B",  (6, 0): "11A",    # A major / F# minor
    (4, 1): "12B",  (1, 0): "12A",    # E major / C# minor
    (11, 1): "1B",  (8, 0): "1A",     # B major / G# minor
    (6, 1): "2B",   (3, 0): "2A",     # F# major / D# minor
    (1, 1): "3B",   (10, 0): "3A",    # C# / Db major / Bb minor
    (8, 1): "4B",   (5, 0): "4A",     # G# / Ab major / F minor
    (3, 1): "5B",   (0, 0): "5A",     # Eb major / C minor
    (10, 1): "6B",  (7, 0): "6A",     # Bb major / G minor
    (5, 1): "7B",   (2, 0): "7A",     # F major / D minor
}


def camelot_code(key: int, mode: int) -> str | None:
    """map (key, mode) pair from spotify audio-features to a Camelot code.

    returns None for the common ``key == -1`` sentinel (no key detected).
    """
    if key is None or key < 0 or key > 11:
        return None
    if mode not in (0, 1):
        return None
    return _CAMELOT.get((int(key), int(mode)))


def _parse_code(code: str) -> tuple[int, str]:
    n = int(code[:-1])
    letter = code[-1]
    return n, letter


def harmonic_distance(a: str | None, b: str | None) -> float:
    """0 = perfect match. 1 = adjacent on the wheel or relative major/minor.
    larger numbers = harsher transition. unknowns score 1.5 (mildly penalized).
    """
    if a is None or b is None:
        return 1.5
    if a == b:
        return 0.0
    an, al = _parse_code(a)
    bn, bl = _parse_code(b)
    ring_dist = min((an - bn) % 12, (bn - an) % 12)
    if al == bl:
        return float(ring_dist)
    # different mode: relative major/minor (same number) is the cheapest cross-mode move
    return 1.0 + float(ring_dist)


def tempo_compatibility(bpm_a: float | None, bpm_b: float | None, window: float = 10.0) -> float:
    """1.0 if within ``window`` BPM, decaying linearly to 0 at 3x window."""
    if bpm_a is None or bpm_b is None or bpm_a <= 0 or bpm_b <= 0:
        return 0.5
    diff = abs(float(bpm_a) - float(bpm_b))
    if diff <= window:
        return 1.0
    if diff >= 3 * window:
        return 0.0
    return float(1.0 - (diff - window) / (2 * window))


def energy_continuity(e_a: float | None, e_b: float | None) -> float:
    """1.0 when energy levels match; drops with |delta|. spotify energy is 0..1."""
    if e_a is None or e_b is None:
        return 0.5
    return float(1.0 - abs(float(e_a) - float(e_b)))


@dataclass
class TrackFeatures:
    track_id: str
    camelot: str | None
    tempo: float | None
    energy: float | None
    valence: float | None
    danceability: float | None
    acousticness: float | None

    def brightness(self) -> float | None:
        """rough timbral brightness: energy / acousticness. higher = brighter."""
        if self.energy is None or self.acousticness is None:
            return None
        denom = max(float(self.acousticness), 0.05)
        return float(self.energy) / denom


def coherence_score(seed: TrackFeatures, candidate: TrackFeatures) -> float:
    """combined musical-coherence score in [0, 1], higher is smoother.

    weights are deliberately simple so it stays interpretable in the UI.
    """
    harm = harmonic_distance(seed.camelot, candidate.camelot)
    harm_score = max(0.0, 1.0 - harm / 6.0)
    tempo = tempo_compatibility(seed.tempo, candidate.tempo)
    energy = energy_continuity(seed.energy, candidate.energy)
    return float(0.5 * harm_score + 0.3 * tempo + 0.2 * energy)


def features_from_row(row) -> TrackFeatures:
    """build TrackFeatures from a pandas row of the audio features csv."""
    key = int(row["key"]) if not _isnan(row.get("key")) else -1
    mode = int(row["mode"]) if not _isnan(row.get("mode")) else -1
    return TrackFeatures(
        track_id=str(row.get("track_id", "")),
        camelot=camelot_code(key, mode),
        tempo=_safe_float(row.get("tempo")),
        energy=_safe_float(row.get("energy")),
        valence=_safe_float(row.get("valence")),
        danceability=_safe_float(row.get("danceability")),
        acousticness=_safe_float(row.get("acousticness")),
    )


def _isnan(x) -> bool:
    try:
        return bool(np.isnan(x))
    except (TypeError, ValueError):
        return x is None


def _safe_float(x) -> float | None:
    try:
        v = float(x)
        if np.isnan(v):
            return None
        return v
    except (TypeError, ValueError):
        return None
