"""dataset assembly: streams from a Source, builds interaction + track
dataframes, splits per-playlist, and constructs sparse matrices.

downstream models read parquet caches written here. nothing in classical.py,
neural.py, or hybrid.py should import sources.py directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from .sources import Source, get_source


@dataclass
class Dataset:
    interactions: pd.DataFrame  # playlist_id, track_id, pos
    tracks: pd.DataFrame  # track_id, track_name, artist_name, album_name, ...
    source_name: str

    def n_playlists(self) -> int:
        return self.interactions["playlist_id"].nunique()

    def n_tracks(self) -> int:
        return self.interactions["track_id"].nunique()


@dataclass
class Splits:
    train: pd.DataFrame
    test: pd.DataFrame  # held-out tail per playlist
    holdout_frac: float


def load_dataset(
    source: str | Source = "mpd",
    cache_dir: str | Path | None = None,
    limit_playlists: int | None = None,
    rebuild: bool = False,
    **source_kwargs,
) -> Dataset:
    """build (or load from parquet cache) a normalized Dataset.

    pass either a source-name string (resolved via get_source) or a Source
    instance directly. caching makes subsequent loads basically free.
    """
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        ix_path = cache_dir / "interactions.parquet"
        tr_path = cache_dir / "tracks.parquet"
        if not rebuild and ix_path.exists() and tr_path.exists():
            return Dataset(
                interactions=pd.read_parquet(ix_path),
                tracks=pd.read_parquet(tr_path),
                source_name=_source_name(source),
            )

    src = get_source(source, **source_kwargs) if isinstance(source, str) else source
    ix_rows: list[tuple[str, str, int]] = []
    track_map: dict[str, dict] = {}

    for pl in src.iter_playlists(limit=limit_playlists):
        for pos, tr in enumerate(pl.tracks):
            if not tr.track_id:
                continue
            ix_rows.append((pl.playlist_id, tr.track_id, pos))
            if tr.track_id not in track_map:
                track_map[tr.track_id] = {
                    "track_id": tr.track_id,
                    "track_name": tr.track_name,
                    "artist_name": tr.artist_name,
                    "album_name": tr.album_name,
                    "artist_id": tr.artist_id,
                    "album_id": tr.album_id,
                }

    interactions = pd.DataFrame(ix_rows, columns=["playlist_id", "track_id", "pos"])
    tracks = pd.DataFrame(list(track_map.values()))

    if cache_dir is not None:
        interactions.to_parquet(cache_dir / "interactions.parquet", index=False)
        tracks.to_parquet(cache_dir / "tracks.parquet", index=False)

    return Dataset(interactions=interactions, tracks=tracks, source_name=src.name)


def split_holdout(
    interactions: pd.DataFrame,
    holdout_frac: float = 0.2,
    min_train: int = 5,
    seed: int = 7,
) -> Splits:
    """per-playlist tail holdout: last holdout_frac of each playlist is test.

    short playlists (<= min_train+1) stay fully in train so we don't end up
    with degenerate users. ordering uses 'pos' if present, else stable order.
    """
    df = interactions.sort_values(["playlist_id", "pos"], kind="stable").reset_index(drop=True)
    grouped = df.groupby("playlist_id", sort=False)
    train_idx: list[int] = []
    test_idx: list[int] = []

    rng = np.random.default_rng(seed)
    for _, g in grouped:
        n = len(g)
        if n <= min_train + 1:
            train_idx.extend(g.index.tolist())
            continue
        cut = max(min_train, int(round(n * (1 - holdout_frac))))
        idxs = g.index.tolist()
        train_idx.extend(idxs[:cut])
        test_idx.extend(idxs[cut:])

    _ = rng  # reserved for future random-tail variants
    return Splits(
        train=df.loc[train_idx].reset_index(drop=True),
        test=df.loc[test_idx].reset_index(drop=True),
        holdout_frac=holdout_frac,
    )


def build_matrix(
    interactions: pd.DataFrame,
    playlist_index: dict[str, int] | None = None,
    track_index: dict[str, int] | None = None,
) -> tuple[sparse.csr_matrix, dict[str, int], dict[str, int]]:
    """sparse playlist-by-track matrix of implicit counts (usually 1).

    returns (matrix, playlist_index, track_index). pass existing indices to
    keep train/test dimensions aligned.
    """
    if playlist_index is None:
        playlist_index = {p: i for i, p in enumerate(interactions["playlist_id"].unique())}
    if track_index is None:
        track_index = {t: i for i, t in enumerate(interactions["track_id"].unique())}

    rows = interactions["playlist_id"].map(playlist_index).to_numpy()
    cols = interactions["track_id"].map(track_index).to_numpy()
    mask = (~pd.isna(rows)) & (~pd.isna(cols))
    rows = rows[mask].astype(np.int32)
    cols = cols[mask].astype(np.int32)
    data = np.ones(len(rows), dtype=np.float32)

    shape = (len(playlist_index), len(track_index))
    mat = sparse.coo_matrix((data, (rows, cols)), shape=shape).tocsr()
    return mat, playlist_index, track_index


def _source_name(source: str | Source) -> str:
    return source if isinstance(source, str) else source.name
