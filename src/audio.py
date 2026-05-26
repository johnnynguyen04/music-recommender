"""spotipy client for playlist lookup only.

we deliberately do NOT call /audio-features here. spotify deprecated that
endpoint for new developer apps in november 2024; the Kaggle dataset under
data/audio_features/ replaces it.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

_PLAYLIST_URL = re.compile(r"playlist[/:]([A-Za-z0-9]+)")


@dataclass(frozen=True)
class FetchedTrack:
    track_id: str
    track_name: str
    artist_name: str
    album_name: str


def parse_playlist_id(url_or_id: str) -> str:
    """accept a full spotify URL, a spotify URI, or a bare playlist id."""
    s = url_or_id.strip()
    m = _PLAYLIST_URL.search(s)
    if m:
        return m.group(1)
    return s


def get_client():
    """authenticated spotipy.Spotify or None if env vars are missing.

    deferred import keeps spotipy out of cold-start paths that don't need it.
    """
    cid = os.environ.get("SPOTIFY_CLIENT_ID")
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not cid or not secret:
        return None
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    auth = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    return spotipy.Spotify(client_credentials_manager=auth, requests_timeout=15)


def fetch_playlist_tracks(url_or_id: str, client: Any | None = None) -> list[FetchedTrack]:
    """fetch tracks from a public spotify playlist by URL or id.

    returns [] if no credentials are configured or the playlist is private.
    """
    sp = client or get_client()
    if sp is None:
        return []

    pid = parse_playlist_id(url_or_id)
    out: list[FetchedTrack] = []
    offset = 0
    while True:
        page = sp.playlist_items(
            pid,
            limit=100,
            offset=offset,
            fields="items(track(id,name,artists(name),album(name))),next",
        )
        for item in page.get("items", []) or []:
            tr = item.get("track") or {}
            tid = tr.get("id")
            if not tid:
                continue
            artists = tr.get("artists") or [{}]
            out.append(
                FetchedTrack(
                    track_id=tid,
                    track_name=tr.get("name", "") or "",
                    artist_name=(artists[0] or {}).get("name", "") or "",
                    album_name=(tr.get("album") or {}).get("name", "") or "",
                )
            )
        if not page.get("next"):
            break
        offset += 100
    return out
