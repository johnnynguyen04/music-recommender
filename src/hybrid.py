"""hybrid recommender: neural CF score + music-theory coherence score.

intuition: collaborative signal answers "who else listens to this", theory
features answer "does this fit smoothly in the playlist's current sonic
neighborhood." we re-rank a wide candidate set (top-N from the CF model) by

    final = alpha * cf_norm + (1 - alpha) * theory_score

theory_score averages coherence_score() over a few "seed" tracks taken from
the tail of the input playlist, so it adapts to the playlist's current mood
instead of locking to a single anchor.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .neural import TrainedNCF, recommend as ncf_recommend
from .theory import TrackFeatures, coherence_score


@dataclass
class HybridConfig:
    alpha: float = 0.7        # weight on cf vs theory; tuned on val set
    candidate_k: int = 200    # how many CF candidates to re-rank
    seed_tail: int = 5        # how many recent tracks define the playlist mood


def _minmax_norm(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def _seed_features(
    seed_track_ids: list[str], features_by_id: dict[str, TrackFeatures]
) -> list[TrackFeatures]:
    return [features_by_id[t] for t in seed_track_ids if t in features_by_id]


def _theory_score_for_candidate(
    candidate: TrackFeatures, seeds: list[TrackFeatures]
) -> float:
    if not seeds:
        return 0.5
    scores = [coherence_score(s, candidate) for s in seeds]
    return float(np.mean(scores))


def _precompute_candidates(
    trained: TrainedNCF,
    playlist_ids: list[str],
    seed_tracks_per_playlist: dict[str, list[str]],
    features_by_id: dict[str, TrackFeatures],
    seen_per_playlist: dict[str, set[str]] | None,
    cfg: HybridConfig,
) -> tuple[list[list[str]], list[np.ndarray], list[np.ndarray]]:
    """return per-playlist (candidates, cf_norm, theory_norm) ready for re-ranking."""
    cf_recs = ncf_recommend(
        trained, playlist_ids, seen_per_playlist=seen_per_playlist, k=cfg.candidate_k,
    )
    candidates_all: list[list[str]] = []
    cf_norms: list[np.ndarray] = []
    theory_norms: list[np.ndarray] = []
    for pid, candidates in zip(playlist_ids, cf_recs, strict=False):
        if not candidates:
            candidates_all.append([])
            cf_norms.append(np.empty(0, dtype=np.float32))
            theory_norms.append(np.empty(0, dtype=np.float32))
            continue
        cf_scores = np.linspace(1.0, 0.0, num=len(candidates), dtype=np.float32)
        tail = (seed_tracks_per_playlist.get(pid) or [])[-cfg.seed_tail :]
        seeds = _seed_features(tail, features_by_id)
        theory_scores = np.array(
            [
                _theory_score_for_candidate(features_by_id.get(t, _UNKNOWN_FEATS), seeds)
                for t in candidates
            ], dtype=np.float32,
        )
        candidates_all.append(candidates)
        cf_norms.append(_minmax_norm(cf_scores))
        theory_norms.append(_minmax_norm(theory_scores))
    return candidates_all, cf_norms, theory_norms


def _rerank(
    candidates_all: list[list[str]],
    cf_norms: list[np.ndarray],
    theory_norms: list[np.ndarray],
    alpha: float,
    k: int,
) -> list[list[str]]:
    out: list[list[str]] = []
    for candidates, cf_n, th_n in zip(candidates_all, cf_norms, theory_norms, strict=False):
        if not candidates:
            out.append([])
            continue
        final = alpha * cf_n + (1.0 - alpha) * th_n
        order = np.argsort(-final)[:k]
        out.append([candidates[i] for i in order])
    return out


def recommend(
    trained: TrainedNCF,
    playlist_ids: list[str],
    seed_tracks_per_playlist: dict[str, list[str]],
    features_by_id: dict[str, TrackFeatures],
    seen_per_playlist: dict[str, set[str]] | None = None,
    cfg: HybridConfig | None = None,
    k: int = 50,
) -> list[list[str]]:
    """return top-K recommendations per playlist using the hybrid score."""
    cfg = cfg or HybridConfig()
    cands, cf_n, th_n = _precompute_candidates(
        trained, playlist_ids, seed_tracks_per_playlist, features_by_id,
        seen_per_playlist, cfg,
    )
    return _rerank(cands, cf_n, th_n, cfg.alpha, k)


def tune_alpha(
    trained: TrainedNCF,
    val_playlist_ids: list[str],
    val_truths: list[set[str]],
    seed_tracks_per_playlist: dict[str, list[str]],
    features_by_id: dict[str, TrackFeatures],
    seen_per_playlist: dict[str, set[str]] | None,
    metric_fn,
    k: int = 10,
    alphas: tuple[float, ...] = (0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
    cfg: HybridConfig | None = None,
) -> tuple[float, dict[float, float]]:
    """grid-search alpha. CF candidates are computed once and reused per alpha."""
    cfg = cfg or HybridConfig()
    cands, cf_n, th_n = _precompute_candidates(
        trained, val_playlist_ids, seed_tracks_per_playlist, features_by_id,
        seen_per_playlist, cfg,
    )
    scores: dict[float, float] = {}
    for a in alphas:
        recs = _rerank(cands, cf_n, th_n, a, k)
        scores[a] = metric_fn(recs, val_truths, k)
    best = max(scores, key=scores.get)
    return best, scores


_UNKNOWN_FEATS = TrackFeatures(
    track_id="",
    camelot=None,
    tempo=None,
    energy=None,
    valence=None,
    danceability=None,
    acousticness=None,
)
