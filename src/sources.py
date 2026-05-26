"""raw-data source adapters that emit a normalized schema.

normalized schema:
  interactions: (playlist_id: str, track_id: str, pos: int)
  tracks:       (track_id: str, track_name: str, artist_name: str,
                 album_name: str, artist_id: str, album_id: str)

new sources just implement Source.iter_playlists() and the loader in
data.py builds the dataframes the rest of the pipeline reads.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Track:
    track_id: str
    track_name: str
    artist_name: str
    album_name: str
    artist_id: str
    album_id: str


@dataclass(frozen=True)
class Playlist:
    playlist_id: str
    tracks: list[Track]


class Source(Protocol):
    """produce playlists one at a time so callers can stream from disk."""

    name: str

    def iter_playlists(self, limit: int | None = None) -> Iterator[Playlist]: ...


class MPDSource:
    """spotify million playlist dataset (mpd) reader.

    expects a directory of ``mpd.slice.X-Y.json`` files. each slice holds
    1000 playlists. iter_playlists streams them so memory stays bounded.
    """

    name = "mpd"

    def __init__(self, slice_dir: str | Path, max_slices: int | None = None):
        self.slice_dir = Path(slice_dir)
        self.max_slices = max_slices

    def slice_files(self) -> list[Path]:
        files = sorted(self.slice_dir.glob("mpd.slice.*.json"), key=_slice_sort_key)
        if self.max_slices is not None:
            files = files[: self.max_slices]
        return files

    def iter_playlists(self, limit: int | None = None) -> Iterator[Playlist]:
        emitted = 0
        for path in self.slice_files():
            with path.open("r", encoding="utf-8") as fh:
                slice_obj = json.load(fh)
            for pl in slice_obj.get("playlists", []):
                yield _to_playlist(pl)
                emitted += 1
                if limit is not None and emitted >= limit:
                    return


def _slice_sort_key(path: Path) -> int:
    # filenames look like mpd.slice.0-999.json; sort by lower bound
    stem = path.stem.replace("mpd.slice.", "")
    return int(stem.split("-")[0])


def _strip_uri(uri: str | None) -> str:
    if not uri:
        return ""
    return uri.split(":")[-1]


def _to_playlist(raw: dict) -> Playlist:
    pid = str(raw.get("pid", ""))
    tracks = [
        Track(
            track_id=_strip_uri(t.get("track_uri")),
            track_name=t.get("track_name", "") or "",
            artist_name=t.get("artist_name", "") or "",
            album_name=t.get("album_name", "") or "",
            artist_id=_strip_uri(t.get("artist_uri")),
            album_id=_strip_uri(t.get("album_uri")),
        )
        for t in raw.get("tracks", [])
    ]
    return Playlist(playlist_id=pid, tracks=tracks)


def get_source(name: str, **kwargs) -> Source:
    """factory; lets configs select a source by short name."""
    name = name.lower()
    if name == "mpd":
        return MPDSource(**kwargs)
    raise ValueError(f"unknown source: {name!r}. known: ['mpd']")
