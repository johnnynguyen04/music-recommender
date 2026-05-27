"""FastAPI inference server. backs the Next.js demo and the FastAPI container.

routes:
  GET  /health                         liveness
  GET  /models                         which models are loaded
  POST /recommend                      body: { playlist_id, recent_track_ids?, model?, k? }
  GET  /search?q=...                   search MPD vocab; returns tracks with album art
  GET  /playlists/sample?n=25          known playlist ids with a preview of their tracks
  GET  /playlists/{pid}/tracks?n=5     first n tracks of a known playlist
  GET  /tracks/{tid}/art               album art URL for a single track (cached)
  POST /tracks/art                     batch album art lookup (body: { track_ids: [...] })
  GET  /metrics                        all metrics JSONs in one blob

album art is fetched from Spotify on demand and cached on disk under `artifacts/art_cache.json`.

run locally:
  uv run uvicorn deploy.serve:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# resolve project root so the server can run from anywhere
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src import audio, neural  # noqa: E402
from src.inference import Recommender, load_features_csv, load_hybrid_alpha  # noqa: E402

ARTIFACTS = Path(os.environ.get("ARTIFACTS_DIR", str(ROOT / "artifacts")))
DATA_PROC = Path(os.environ.get("DATA_PROC_DIR", str(ROOT / "data" / "processed")))
DATA_AUDIO = Path(os.environ.get("DATA_AUDIO_CSV", str(ROOT / "data" / "audio_features" / "dataset.csv")))
RESULTS_M = Path(os.environ.get("RESULTS_METRICS", str(ROOT / "results" / "metrics")))
ART_CACHE = ARTIFACTS / "art_cache.json"

CORS_ALLOWED = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.environ.get("FRONTEND_ORIGIN", "*"),
]

app = FastAPI(title="music-recommender API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rec: Recommender | None = None
_tracks: pd.DataFrame | None = None
_art_cache: dict[str, str | None] = {}
_spotify = None  # spotipy client; lazy


class RecommendIn(BaseModel):
    playlist_id: str
    recent_track_ids: list[str] = []
    seen_track_ids: list[str] = []
    model: Literal["neural", "hybrid"] = "hybrid"
    k: int = 10


class ArtBatchIn(BaseModel):
    track_ids: list[str]


@app.on_event("startup")
def _load():
    global _rec, _tracks, _art_cache, _spotify
    _maybe_download_from_s3()
    ncf_path = ARTIFACTS / "ncf.pt"
    tracks_path = DATA_PROC / "tracks.parquet"
    if not (ncf_path.exists() and tracks_path.exists()):
        print(f"[startup] artifacts not found (ncf={ncf_path.exists()}, tracks={tracks_path.exists()})")
        return
    _tracks = pd.read_parquet(tracks_path)
    ncf = neural.load(ncf_path)
    feats = load_features_csv(DATA_AUDIO) if DATA_AUDIO.exists() else {}
    alpha = load_hybrid_alpha(RESULTS_M / "hybrid.json")
    _rec = Recommender(
        cf_model=None, train_matrix=None, ncf=ncf,
        tracks=_tracks, features_by_id=feats, hybrid_alpha=alpha,
    )
    if ART_CACHE.exists():
        try:
            raw = json.loads(ART_CACHE.read_text())
        except json.JSONDecodeError:
            raw = {}
        # migrate old cache (str values were just art URLs, no preview)
        _art_cache = {}
        for tid, v in raw.items():
            if isinstance(v, dict):
                _art_cache[tid] = v
            elif isinstance(v, str) or v is None:
                _art_cache[tid] = {"art_url": v, "preview_url": None}
    _spotify = audio.get_client()
    print(f"[startup] loaded. {len(_tracks):,} tracks, alpha={alpha}, "
          f"art_cache={len(_art_cache):,}, spotify={'on' if _spotify else 'off'}")


def _maybe_download_from_s3():
    bucket = os.environ.get("MODEL_BUCKET")
    if not bucket:
        return
    import boto3
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    target = ARTIFACTS / "ncf.pt"
    if target.exists():
        return
    try:
        s3.download_file(bucket, "ncf.pt", str(target))
        print(f"[startup] pulled ncf.pt from s3://{bucket}/")
    except Exception as e:
        print(f"[startup] s3 download skipped: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "loaded": _rec is not None}


@app.get("/models")
def models():
    if _rec is None:
        return {"available": []}
    return {"available": ["neural", "hybrid"]}


@app.post("/recommend")
def recommend(body: RecommendIn):
    if _rec is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    recs = _rec.recommend(
        body.playlist_id,
        recent_track_ids=body.recent_track_ids,
        seen_track_ids=set(body.seen_track_ids),
        model=body.model,
        k=body.k,
    )
    # attach album art + 30s preview URL (best-effort, both can be null)
    meta = _batch_meta([r["track_id"] for r in recs])
    for r in recs:
        info = meta.get(r["track_id"]) or {}
        r["art_url"] = info.get("art_url")
        r["preview_url"] = info.get("preview_url")
    return {"model": body.model, "playlist_id": body.playlist_id, "recommendations": recs}


@app.get("/search")
def search(q: str, limit: int = 8):
    if _tracks is None:
        raise HTTPException(status_code=503, detail="catalog not loaded")
    if not q.strip():
        return {"results": []}
    needle = q.strip().lower()
    haystack = (_tracks["artist_name"].fillna("").str.lower() + " " +
                _tracks["track_name"].fillna("").str.lower())
    hits = _tracks[haystack.str.contains(needle, regex=False, na=False)].head(limit)
    items = hits[["track_id", "artist_name", "track_name", "album_name"]].to_dict("records")
    meta = _batch_meta([i["track_id"] for i in items])
    for i in items:
        info = meta.get(i["track_id"]) or {}
        i["art_url"] = info.get("art_url")
        i["preview_url"] = info.get("preview_url")
    return {"results": items}


@app.get("/playlists/sample")
def playlists_sample(n: int = 25):
    if _rec is None or _rec.ncf is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    pids = list(_rec.ncf.playlist_index.keys())[:n]
    inter = _interactions_cache()
    out = []
    for pid in pids:
        track_ids = inter.get(pid, [])[:3]
        preview = []
        if track_ids and _tracks is not None:
            rows = _tracks.set_index("track_id").reindex(track_ids).reset_index()
            for _, r in rows.iterrows():
                preview.append({
                    "artist": r.get("artist_name"),
                    "title": r.get("track_name"),
                })
        out.append({"playlist_id": pid, "preview": preview})
    return {"playlists": out}


@app.get("/playlists/{pid}/tracks")
def playlist_tracks(pid: str, n: int = 5):
    inter = _interactions_cache()
    tids = inter.get(pid, [])[:n]
    if not tids or _tracks is None:
        return {"tracks": []}
    rows = _tracks.set_index("track_id").reindex(tids).reset_index()
    meta = _batch_meta(tids)
    out = []
    for _, r in rows.iterrows():
        tid = r["track_id"]
        info = meta.get(tid) or {}
        out.append({
            "track_id": tid,
            "artist_name": r.get("artist_name"),
            "track_name": r.get("track_name"),
            "art_url": info.get("art_url"),
            "preview_url": info.get("preview_url"),
        })
    return {"tracks": out}


@app.get("/tracks/{tid}/art")
def track_art(tid: str):
    info = _batch_meta([tid]).get(tid) or {}
    return {"track_id": tid, **info}


@app.post("/tracks/art")
def tracks_art(body: ArtBatchIn):
    return {"meta": _batch_meta(body.track_ids)}


@app.get("/metrics")
def metrics_all():
    out = {}
    for name in ("classical", "neural", "hybrid", "comparison", "match_rate"):
        p = RESULTS_M / f"{name}.json"
        if p.exists():
            out[name] = json.loads(p.read_text())
    return out


# ----- internal helpers -----

_inter_cache: dict[str, list[str]] | None = None


def _interactions_cache() -> dict[str, list[str]]:
    global _inter_cache
    if _inter_cache is None:
        path = DATA_PROC / "interactions.parquet"
        if not path.exists():
            _inter_cache = {}
            return _inter_cache
        df = pd.read_parquet(path)
        _inter_cache = df.sort_values(["playlist_id", "pos"]).groupby("playlist_id")["track_id"].apply(list).to_dict()
    return _inter_cache


def _batch_meta(track_ids: list[str]) -> dict[str, dict]:
    """fetch album art URL + 30s preview URL for a batch.

    spotify locked /tracks for new dev-mode apps so we use /search by name+artist.
    parallelized with a small thread pool; cached on disk per-track. result shape:
      {tid: {"art_url": str|None, "preview_url": str|None}}
    """
    out: dict[str, dict] = {}
    missing: list[str] = []
    for tid in track_ids:
        if tid in _art_cache:
            out[tid] = _art_cache[tid]
        else:
            missing.append(tid)

    if not missing or _spotify is None or _tracks is None:
        for tid in missing:
            out[tid] = {"art_url": None, "preview_url": None}
        return out

    meta = _tracks.set_index("track_id").reindex(missing).reset_index()
    queries = []
    for _, row in meta.iterrows():
        tid = row["track_id"]
        artist = (row.get("artist_name") or "").strip()
        title = (row.get("track_name") or "").strip()
        if not artist or not title:
            _art_cache[tid] = {"art_url": None, "preview_url": None}
            out[tid] = _art_cache[tid]
            continue
        queries.append((tid, artist, title))

    if queries:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(_lookup_meta_one, queries))
        for (tid, _, _), info in zip(queries, results, strict=True):
            _art_cache[tid] = info
            out[tid] = info
        _flush_art_cache()
    return out


def _lookup_meta_one(qtup: tuple[str, str, str]) -> dict:
    _tid, artist, title = qtup
    # iTunes Search API: free, no auth, returns 30s previewUrl and album art.
    # spotify removed preview_url from /search for dev-mode apps in late 2024,
    # and iTunes covers basically every commercial track in MPD anyway.
    import urllib.parse, urllib.request

    term = urllib.parse.quote_plus(f"{artist} {title}")
    url = f"https://itunes.apple.com/search?term={term}&entity=song&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"art_url": None, "preview_url": None}
    results = data.get("results") or []
    if not results:
        return {"art_url": None, "preview_url": None}
    r = results[0]
    # iTunes returns 100x100 art by default; bump to 300x300 by URL substitution
    art = r.get("artworkUrl100")
    if art:
        art = art.replace("100x100bb", "300x300bb")
    return {"art_url": art, "preview_url": r.get("previewUrl")}


def _flush_art_cache():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    try:
        ART_CACHE.write_text(json.dumps(_art_cache))
    except OSError as e:
        print(f"[art] could not write cache: {e}")
