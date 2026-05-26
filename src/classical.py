"""classical collaborative filtering baseline.

wraps implicit ALS so it returns top-K track-id lists for arbitrary playlist
indices. also a TruncatedSVD fallback for environments where the implicit
wheel won't install.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse


@dataclass
class CFModel:
    factors: int
    iterations: int
    regularization: float
    alpha: float
    backend: str  # "als" or "svd"
    track_index: dict[str, int]
    playlist_index: dict[str, int]
    item_factors: np.ndarray
    user_factors: np.ndarray

    def reverse_track_index(self) -> list[str]:
        ids = [""] * len(self.track_index)
        for tid, i in self.track_index.items():
            ids[i] = tid
        return ids


def fit_als(
    matrix: sparse.csr_matrix,
    playlist_index: dict[str, int],
    track_index: dict[str, int],
    factors: int = 64,
    iterations: int = 15,
    regularization: float = 0.01,
    alpha: float = 40.0,
    use_gpu: bool = False,
) -> CFModel:
    """implicit ALS on the playlist-track confidence matrix.

    implicit expects user-item; here users = playlists, items = tracks.
    """
    from implicit.als import AlternatingLeastSquares

    model = AlternatingLeastSquares(
        factors=factors,
        iterations=iterations,
        regularization=regularization,
        use_gpu=use_gpu,
    )
    model.fit((matrix * alpha).astype(np.float32))
    return CFModel(
        factors=factors,
        iterations=iterations,
        regularization=regularization,
        alpha=alpha,
        backend="als",
        track_index=track_index,
        playlist_index=playlist_index,
        item_factors=np.asarray(model.item_factors),
        user_factors=np.asarray(model.user_factors),
    )


def fit_svd(
    matrix: sparse.csr_matrix,
    playlist_index: dict[str, int],
    track_index: dict[str, int],
    factors: int = 64,
) -> CFModel:
    """TruncatedSVD fallback. weaker but always installs."""
    from sklearn.decomposition import TruncatedSVD

    svd = TruncatedSVD(n_components=factors, random_state=7)
    user_factors = svd.fit_transform(matrix)
    item_factors = svd.components_.T
    return CFModel(
        factors=factors,
        iterations=0,
        regularization=0.0,
        alpha=1.0,
        backend="svd",
        track_index=track_index,
        playlist_index=playlist_index,
        item_factors=item_factors.astype(np.float32),
        user_factors=user_factors.astype(np.float32),
    )


def recommend(
    model: CFModel,
    train_matrix: sparse.csr_matrix,
    playlist_ids: list[str],
    k: int = 50,
    filter_already_seen: bool = True,
    batch_size: int = 256,
) -> list[list[str]]:
    """top-K track ids per playlist, with seen tracks optionally masked out.

    batched to avoid pathological per-playlist BLAS overhead on large catalogs.
    """
    reverse_tracks = model.reverse_track_index()
    item_t = model.item_factors.T  # (D, n_items)

    valid: list[tuple[int, int]] = []  # (output_position, internal_idx)
    out: list[list[str]] = [[] for _ in playlist_ids]
    for out_i, pid in enumerate(playlist_ids):
        idx = model.playlist_index.get(pid)
        if idx is not None:
            valid.append((out_i, idx))

    for start in range(0, len(valid), batch_size):
        chunk = valid[start : start + batch_size]
        user_idx = np.array([i for _, i in chunk], dtype=np.int32)
        users = model.user_factors[user_idx]                # (B, D)
        scores = users @ item_t                              # (B, n_items)
        if filter_already_seen:
            for row, (_, i) in enumerate(chunk):
                seen = train_matrix[i].indices
                if len(seen):
                    scores[row, seen] = -np.inf
        # argpartition then sort the top-k slice (much faster than full sort)
        top_k_unsorted = np.argpartition(-scores, k, axis=1)[:, :k]
        for row, (out_i, _) in enumerate(chunk):
            cols = top_k_unsorted[row]
            order = np.argsort(-scores[row, cols])
            out[out_i] = [reverse_tracks[j] for j in cols[order]]
    return out
