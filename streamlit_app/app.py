"""music recommender demo: classical CF vs neural CF vs theory-aware hybrid.

run locally:
  uv run streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import audio, neural  # noqa: E402
from src.inference import Recommender, load_features_csv  # noqa: E402
from streamlit_app import camelot  # noqa: E402
from streamlit_app.style import PALETTE, inject_css  # noqa: E402

load_dotenv(ROOT / ".env")

ARTIFACTS = ROOT / "artifacts"
DATA_PROC = ROOT / "data" / "processed"
DATA_AUDIO = ROOT / "data" / "audio_features" / "dataset.csv"
RESULTS_M = ROOT / "results" / "metrics"
RESULTS_F = ROOT / "results" / "figures"


st.set_page_config(page_title="music recommender", page_icon="·", layout="centered")
st.markdown(inject_css(), unsafe_allow_html=True)


@st.cache_resource
def _bootstrap() -> Recommender | None:
    ncf_path = ARTIFACTS / "ncf.pt"
    tracks_path = DATA_PROC / "tracks.parquet"
    if not ncf_path.exists() or not tracks_path.exists():
        return None
    tracks = pd.read_parquet(tracks_path)
    ncf = neural.load(ncf_path)
    feats = load_features_csv(DATA_AUDIO) if DATA_AUDIO.exists() else {}
    return Recommender(
        cf_model=None,            # streamlit demo focuses on neural + hybrid
        train_matrix=None,
        ncf=ncf,
        tracks=tracks,
        features_by_id=feats,
    )


@st.cache_data
def _load_metrics() -> dict:
    out = {}
    for name in ("classical", "neural", "hybrid", "comparison", "match_rate"):
        p = RESULTS_M / f"{name}.json"
        if p.exists():
            out[name] = json.loads(p.read_text())
    return out


def _header():
    st.markdown("<h1>music recommender</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='lede'>three models, same playlists, same test split. classical "
        "matrix factorization, a two-tower neural net, and a hybrid that re-ranks "
        "by music-theory compatibility. built to compare honestly, not to win a "
        "leaderboard.</p>",
        unsafe_allow_html=True,
    )


def _tab_try(rec: Recommender | None):
    st.markdown("<h2>try the recommender</h2>", unsafe_allow_html=True)
    if rec is None:
        st.info("no trained artifacts found. run `uv run python scripts/run_pipeline.py` first.")
        return

    seed_pids = list(rec.ncf.playlist_index.keys())[:25] if rec.ncf else []
    col1, col2 = st.columns([3, 2])
    with col1:
        url = st.text_input(
            "spotify playlist url (optional)",
            placeholder="https://open.spotify.com/playlist/...",
            label_visibility="visible",
        )
    with col2:
        sample_pid = st.selectbox(
            "or pick a known playlist id (from MPD)",
            options=[""] + seed_pids,
            index=0,
        )

    model_choice = st.radio("model", ["hybrid", "neural", "classical"], horizontal=True, index=0)
    k = st.slider("how many recommendations", 5, 25, 10)

    if not st.button("recommend"):
        return

    recent: list[str] = []
    pid = sample_pid
    if url:
        fetched = audio.fetch_playlist_tracks(url)
        if not fetched:
            st.warning("could not fetch that playlist. is it public? are SPOTIFY_CLIENT_ID/_SECRET set?")
        recent = [t.track_id for t in fetched]
        st.caption(f"pulled {len(recent)} tracks from spotify")
        if recent and rec.ncf and pid not in rec.ncf.playlist_index:
            # cold-start: no known playlist embedding. fall back to hybrid with seeds.
            pid = recent[0] if recent else ""

    if not pid:
        st.warning("either paste a spotify url or pick a sample playlist id.")
        return

    recs = rec.recommend(pid, recent_track_ids=recent, model=model_choice, k=k)
    if not recs:
        st.error("no recommendations produced. check the logs.")
        return

    st.markdown("<h3>recommendations</h3>", unsafe_allow_html=True)
    for i, r in enumerate(recs, start=1):
        title = r.get("track_name") or r.get("track_id")
        artist = r.get("artist_name", "")
        cam = r.get("camelot") or "?"
        tempo = r.get("tempo")
        bpm = f"{tempo:.0f} BPM" if isinstance(tempo, (int, float)) else "? BPM"
        coh = r.get("coherence")
        coh_str = f"coherence {coh:.2f}" if isinstance(coh, (int, float)) else ""
        st.markdown(
            f"""<div class="card rec-card">
                <div class="rec-rank">{i:02d}</div>
                <div>
                  <div class="rec-title">{title}</div>
                  <div class="rec-artist">{artist}</div>
                </div>
                <div class="rec-meta">{cam} · {bpm}<br/>{coh_str}</div>
              </div>""",
            unsafe_allow_html=True,
        )


def _tab_why(metrics: dict):
    st.markdown("<h2>why these songs</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p>each hybrid recommendation has two parts: a collaborative-filter "
        "score from the neural model (who else listens to this) and a music-theory "
        "coherence score (does it sit well next to your recent tracks). final "
        "rank is <span class='mono'>α · cf + (1−α) · theory</span>.</p>",
        unsafe_allow_html=True,
    )
    if "hybrid" in metrics:
        alpha = metrics["hybrid"].get("alpha")
        st.markdown(
            f"<span class='badge'>α = {alpha}</span> tuned on a held-out validation split.",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<p>coherence breaks down into harmonic distance on the Camelot wheel, "
        "tempo proximity, and energy continuity. these are crude proxies for "
        "what a DJ would consider when sequencing tracks, not a perceptual "
        "model.</p>",
        unsafe_allow_html=True,
    )


def _tab_metrics(metrics: dict):
    st.markdown("<h2>model comparison</h2>", unsafe_allow_html=True)
    comp = metrics.get("comparison")
    if not comp:
        st.info("metrics not generated yet. run the pipeline.")
        return
    keys = list(comp["classical"].keys())
    rows = []
    for m in ("classical", "neural", "hybrid"):
        rows.append({"model": m, **{k: comp[m][k] for k in keys}})
    df = pd.DataFrame(rows).set_index("model")
    st.dataframe(df.style.format("{:.4f}"), use_container_width=True)
    img = RESULTS_F / "comparison.png"
    if img.exists():
        st.image(str(img), use_column_width=True)
    st.caption(
        f"evaluated on {comp.get('eval_playlists', '?')} held-out playlists. "
        f"audio-feature match rate: {comp.get('audio_feature_match_rate', 0):.1%}."
    )


def _tab_theory():
    st.markdown("<h2>music theory in action</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p>the Camelot wheel maps every key to a number 1-12 with an A (minor) "
        "or B (major) suffix. keys that share a face or sit next to each other "
        "on the wheel share most of their notes, so cuts between them sound "
        "smooth. moves across the wheel sound abrupt unless they are "
        "intentional.</p>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([3, 2])
    with col1:
        fig = camelot.draw(
            track_codes=["8B", "9B", "10B", "5A", "12A"],
            highlight="8B",
            title="example: tracks in C / G / D major plus two soft minors",
        )
        st.pyplot(fig, clear_figure=True)
    with col2:
        st.markdown(
            "<p><span class='badge'>·</span> the gold star marks the seed track key.<br/>"
            "<span class='badge'>·</span> burgundy dots are candidate keys.<br/>"
            "<span class='badge'>·</span> adjacency on the wheel = harmonic distance ≈ 1.</p>",
            unsafe_allow_html=True,
        )


def _tab_methodology(metrics: dict):
    st.markdown("<h2>methodology</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <p>i was a music major before switching to data science at UCF. that left
        a stack of theory, ear-training, and music-tech coursework that doesn't
        usually show up in a DS portfolio. this project puts it to work.</p>

        <p>the data is the Spotify Million Playlist Dataset; the audio features
        are a Kaggle pre-fetch (Spotify deprecated the audio-features endpoint
        for new developer apps in late 2024). per-playlist holdout splits the
        last 20% of each playlist as test, then half of that is held back again
        as validation for tuning the hybrid weight.</p>

        <p>the three models are scored on the same playlists and the same metric
        set: NDCG, hit rate, precision, and recall at K = 10 and K = 50. nothing
        is dropped from the comparison table.</p>
        """,
        unsafe_allow_html=True,
    )
    if "match_rate" in metrics:
        mr = metrics["match_rate"]
        st.markdown(
            f"<p class='mono'>audio feature coverage: "
            f"{mr['matched']:,} / {mr['total_mpd_tracks']:,} tracks "
            f"({mr['match_rate']:.1%})</p>",
            unsafe_allow_html=True,
        )


def _tab_about():
    st.markdown("<h2>about</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <p>built by Johnny Nguyen, UCF data science class of 2027. source code,
        training scripts, and a longer write-up live on
        <a href='https://github.com/johnnynguyen04/music-recommender' style='color:#8b3a3a'>
        github.com/johnnynguyen04/music-recommender</a>.</p>
        """,
        unsafe_allow_html=True,
    )


def main():
    _header()
    rec = _bootstrap()
    metrics = _load_metrics()
    tabs = st.tabs([
        "try it", "why these songs", "model comparison",
        "music theory", "methodology", "about",
    ])
    with tabs[0]: _tab_try(rec)
    with tabs[1]: _tab_why(metrics)
    with tabs[2]: _tab_metrics(metrics)
    with tabs[3]: _tab_theory()
    with tabs[4]: _tab_methodology(metrics)
    with tabs[5]: _tab_about()


if __name__ == "__main__":
    main()
