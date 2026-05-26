"""minimal FastAPI inference endpoint.

three routes:
  GET  /health                 -> liveness
  POST /recommend              -> body: { playlist_id, recent_track_ids?, model?, k? }
  GET  /models                 -> which models are loaded

artifacts are pulled from S3 at boot if env vars are set, else loaded from
local paths.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import boto3
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src import neural
from src.inference import Recommender, load_features_csv

ARTIFACTS = Path(os.environ.get("ARTIFACTS_DIR", "/app/artifacts"))
DATA_PROC = Path(os.environ.get("DATA_PROC_DIR", "/app/data/processed"))
DATA_AUDIO = Path(os.environ.get("DATA_AUDIO_CSV", "/app/data/audio_features/dataset.csv"))

app = FastAPI(title="music-recommender")
_rec: Recommender | None = None


class RecommendIn(BaseModel):
    playlist_id: str
    recent_track_ids: list[str] = []
    seen_track_ids: list[str] = []
    model: Literal["neural", "hybrid"] = "hybrid"
    k: int = 10


@app.on_event("startup")
def _load():
    global _rec
    _maybe_download_from_s3()
    ncf_path = ARTIFACTS / "ncf.pt"
    tracks_path = DATA_PROC / "tracks.parquet"
    if not (ncf_path.exists() and tracks_path.exists()):
        return
    ncf = neural.load(ncf_path)
    tracks = pd.read_parquet(tracks_path)
    feats = load_features_csv(DATA_AUDIO) if DATA_AUDIO.exists() else {}
    _rec = Recommender(
        cf_model=None, train_matrix=None, ncf=ncf,
        tracks=tracks, features_by_id=feats,
    )


def _maybe_download_from_s3():
    bucket = os.environ.get("MODEL_BUCKET")
    if not bucket:
        return
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    try:
        s3.download_file(bucket, "ncf.pt", str(ARTIFACTS / "ncf.pt"))
    except Exception as e:
        print(f"s3 download skipped: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "loaded": _rec is not None}


@app.get("/models")
def models():
    if _rec is None:
        return {"available": []}
    out = []
    if _rec.ncf is not None: out += ["neural", "hybrid"]
    return {"available": out}


@app.post("/recommend")
def recommend(body: RecommendIn):
    if _rec is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    return {
        "model": body.model,
        "playlist_id": body.playlist_id,
        "recommendations": _rec.recommend(
            body.playlist_id,
            recent_track_ids=body.recent_track_ids,
            seen_track_ids=set(body.seen_track_ids),
            model=body.model,
            k=body.k,
        ),
    }
