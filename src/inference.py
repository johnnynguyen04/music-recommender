"""serving-time wrapper that holds all three trained models and exposes one
``recommend()`` call used by the streamlit demo and any HTTP service.

we don't retrain at request time; everything here is read-only once the
artifacts are loaded.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from scipy import sparse

from . import classical, hybrid, neural
from .theory import TrackFeatures, features_from_row

ModelName = Literal["classical", "neural", "hybrid"]


@dataclass
class Recommender:
    cf_model: classical.CFModel | None
    train_matrix: sparse.csr_matrix | None
    ncf: neural.TrainedNCF | None
    tracks: pd.DataFrame
    features_by_id: dict[str, TrackFeatures]

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

        if model == "classical":
            if self.cf_model is None or self.train_matrix is None:
                return []
            recs = classical.recommend(
                self.cf_model,
                self.train_matrix,
                [playlist_id],
                k=k,
            )[0]
        elif model == "neural":
            if self.ncf is None:
                return []
            recs = neural.recommend(
                self.ncf,
                [playlist_id],
                seen_per_playlist={playlist_id: seen_track_ids},
                k=k,
            )[0]
        elif model == "hybrid":
            if self.ncf is None:
                return []
            recs = hybrid.recommend(
                self.ncf,
                [playlist_id],
                seed_tracks_per_playlist={playlist_id: recent_track_ids},
                features_by_id=self.features_by_id,
                seen_per_playlist={playlist_id: seen_track_ids},
                k=k,
            )[0]
        else:
            raise ValueError(f"unknown model: {model!r}")

        return self._annotate(recs, recent_track_ids)

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
