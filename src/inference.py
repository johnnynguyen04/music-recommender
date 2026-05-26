"""serving-time wrapper that holds all three trained models and exposes one
``recommend()`` call used by the streamlit demo and any HTTP service.

we don't retrain at request time; everything here is read-only once the
artifacts are loaded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from scipy import sparse

from . import classical, hybrid, neural
from .theory import TrackFeatures, coherence_score, features_from_row

ModelName = Literal["classical", "neural", "hybrid"]


@dataclass
class Recommender:
    cf_model: classical.CFModel | None
    train_matrix: sparse.csr_matrix | None
    ncf: neural.TrainedNCF | None
    tracks: pd.DataFrame
    features_by_id: dict[str, TrackFeatures]
    hybrid_alpha: float = 0.9  # default; load_hybrid_alpha() pulls the tuned value

    def known_playlist(self, pid: str) -> bool:
        if self.ncf is not None and pid in self.ncf.playlist_index:
            return True
        if self.cf_model is not None and pid in self.cf_model.playlist_index:
            return True
        return False

    def recommend(
        self,
        playlist_id: str,
        recent_track_ids: list[str] | None = None,
        seen_track_ids: set[str] | None = None,
        model: ModelName = "hybrid",
        k: int = 10,
    ) -> list[dict]:
        recent_track_ids = recent_track_ids or []
        seen_track_ids = seen_track_ids or set()

        # cold-start: unknown playlist + at least one seed track. mean-pool the
        # seed track embeddings to make a synthetic playlist vector.
        if self.ncf is not None and recent_track_ids and not self.known_playlist(playlist_id):
            recs = self._cold_recommend(recent_track_ids, seen_track_ids, model, k)
            return self._annotate(recs, recent_track_ids)

        if model == "classical":
            if self.cf_model is None or self.train_matrix is None:
                return []
            recs = classical.recommend(
                self.cf_model, self.train_matrix, [playlist_id], k=k,
            )[0]
        elif model == "neural":
            if self.ncf is None:
                return []
            recs = neural.recommend(
                self.ncf, [playlist_id],
                seen_per_playlist={playlist_id: seen_track_ids}, k=k,
            )[0]
        elif model == "hybrid":
            if self.ncf is None:
                return []
            recs = hybrid.recommend(
                self.ncf, [playlist_id],
                seed_tracks_per_playlist={playlist_id: recent_track_ids},
                features_by_id=self.features_by_id,
                seen_per_playlist={playlist_id: seen_track_ids},
                cfg=hybrid.HybridConfig(alpha=self.hybrid_alpha),
                k=k,
            )[0]
        else:
            raise ValueError(f"unknown model: {model!r}")

        return self._annotate(recs, recent_track_ids)

    def _cold_recommend(
        self,
        seed_track_ids: list[str],
        seen_track_ids: set[str],
        model: ModelName,
        k: int,
    ) -> list[str]:
        """recommend from a synthetic user vector built by mean-pooling seed tracks."""
        ncf = self.ncf
        item_w = ncf.model.track_emb.weight.detach().cpu().numpy()
        # pick out the seed track embeddings that the model actually knows
        seed_idx = [ncf.track_index[t] for t in seed_track_ids if t in ncf.track_index]
        if not seed_idx:
            return []
        user_vec = item_w[seed_idx].mean(axis=0)
        scores = item_w @ user_vec
        # mask seeds and any explicit "seen" tracks
        for j in seed_idx:
            scores[j] = -np.inf
        for t in seen_track_ids:
            j = ncf.track_index.get(t)
            if j is not None:
                scores[j] = -np.inf

        cand_k = max(k * 20, 100) if model == "hybrid" else k
        top = np.argpartition(-scores, cand_k)[:cand_k]
        top = top[np.argsort(-scores[top])]
        reverse = ncf.reverse_track_index()
        candidates = [reverse[j] for j in top]

        if model != "hybrid":
            return candidates[:k]

        # hybrid re-rank: blend CF rank position with theory coherence vs seeds
        cf_norm = np.linspace(1.0, 0.0, num=len(candidates), dtype=np.float32)
        seed_feats = [self.features_by_id[t] for t in seed_track_ids
                      if t in self.features_by_id]
        if not seed_feats:
            return candidates[:k]
        theory = np.array(
            [_mean_coherence(self.features_by_id.get(t), seed_feats) for t in candidates],
            dtype=np.float32,
        )
        cf_n = _minmax(cf_norm)
        th_n = _minmax(theory)
        final = self.hybrid_alpha * cf_n + (1.0 - self.hybrid_alpha) * th_n
        order = np.argsort(-final)[:k]
        return [candidates[i] for i in order]

    def _annotate(self, track_ids: list[str], recent_track_ids: list[str]) -> list[dict]:
        meta = self.tracks.set_index("track_id")
        seed_feats = [
            self.features_by_id[t] for t in recent_track_ids[-5:] if t in self.features_by_id
        ]
        rows: list[dict] = []
        for tid in track_ids:
            base = {"track_id": tid}
            if tid in meta.index:
                m = meta.loc[tid]
                base.update(
                    {
                        "track_name": m.get("track_name", ""),
                        "artist_name": m.get("artist_name", ""),
                        "album_name": m.get("album_name", ""),
                    }
                )
            feat = self.features_by_id.get(tid)
            if feat is not None:
                base.update(
                    {
                        "camelot": feat.camelot,
                        "tempo": feat.tempo,
                        "energy": feat.energy,
                    }
                )
                if seed_feats:
                    from .theory import coherence_score
                    base["coherence"] = float(
                        np.mean([coherence_score(s, feat) for s in seed_feats])
                    )
            rows.append(base)
        return rows


def load_features_csv(path: str | Path) -> dict[str, TrackFeatures]:
    """build a track_id -> TrackFeatures map from the kaggle dataset csv."""
    df = pd.read_csv(path)
    feats: dict[str, TrackFeatures] = {}
    for _, row in df.iterrows():
        tf = features_from_row(row)
        if tf.track_id:
            feats[tf.track_id] = tf
    return feats


def load_hybrid_alpha(metrics_path: str | Path, default: float = 0.9) -> float:
    """read the tuned alpha from results/metrics/hybrid.json if present."""
    p = Path(metrics_path)
    if not p.exists():
        return default
    try:
        return float(json.loads(p.read_text()).get("alpha", default))
    except (ValueError, KeyError):
        return default


def _mean_coherence(candidate_feat, seed_feats: list[TrackFeatures]) -> float:
    if candidate_feat is None or not seed_feats:
        return 0.5
    return float(np.mean([coherence_score(s, candidate_feat) for s in seed_feats]))


def _minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)
