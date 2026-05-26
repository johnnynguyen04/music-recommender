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
from src.inference import Recommender, load_features_csv, load_hybrid_alpha  # noqa: E402
from streamlit_app import camelot  # noqa: E402
from streamlit_app.style import PALETTE, inject_css  # noqa: E402

load_dotenv(ROOT / ".env")

ARTIFACTS = ROOT / "artifacts"
DATA_PROC = ROOT / "data" / "processed"
DATA_AUDIO = ROOT / "data" / "audio_features" / "dataset.csv"
RESULTS_M = ROOT / "results" / "metrics"
RESULTS_F = ROOT / "results" / "figures"


st.set_page_config(page_title="Music Recommender", page_icon="·", layout="centered")
st.markdown(inject_css(), unsafe_allow_html=True)

MODEL_LABELS = {"hybrid": "Music-aware", "neural": "Pattern only"}
MODEL_HELP = {
    "hybrid": "Looks at what songs people group together, then double-checks that each suggestion fits your seeds' key, tempo, and energy.",
    "neural": "Looks at what songs people group together. No music-theory check.",
}


@st.cache_resource
def _bootstrap() -> Recommender | None:
    ncf_path = ARTIFACTS / "ncf.pt"
    tracks_path = DATA_PROC / "tracks.parquet"
    if not ncf_path.exists() or not tracks_path.exists():
        return None
    tracks = pd.read_parquet(tracks_path)
    ncf = neural.load(ncf_path)
    feats = load_features_csv(DATA_AUDIO) if DATA_AUDIO.exists() else {}
    alpha = load_hybrid_alpha(RESULTS_M / "hybrid.json")
    return Recommender(
        cf_model=None,            # streamlit demo focuses on neural + hybrid
        train_matrix=None,
        ncf=ncf,
        tracks=tracks,
        features_by_id=feats,
        hybrid_alpha=alpha,
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
    st.markdown("<h1>Music Recommender</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='lede'>Pick a few songs you like. Two models try to guess what "
        "fits next. One leans entirely on what other people put together in their "
        "playlists. The other does that too, then adds a music-theory check on top. "
        "The whole thing is here so you can see the difference.</p>",
        unsafe_allow_html=True,
    )


def _tab_try(rec: Recommender | None):
    st.markdown("<h2>Try it</h2>", unsafe_allow_html=True)
    if rec is None:
        st.info("No trained artifacts found. Run `uv run python scripts/run_pipeline.py` first.")
        return

    if "seed_tracks" not in st.session_state:
        st.session_state.seed_tracks = []  # list[(track_id, artist, title)]

    st.markdown(
        "<p>Pick songs you like, choose a model, and see what gets suggested next.</p>",
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Input mode",
        ["Search for songs", "Pick a sample playlist", "Paste a Spotify URL"],
        horizontal=True,
        label_visibility="collapsed",
    )

    pid = ""
    recent: list[str] = []

    if mode == "Search for songs":
        st.caption(
            "The model was trained on Spotify playlists from 2010 to 2017, so newer songs won't show up. "
            "Try things like 'wagon wheel', 'lorde royals', or 'kanye'."
        )
        q = st.text_input("Search", placeholder="Search by song or artist", label_visibility="collapsed")
        if q:
            results = _search_mpd_vocab(rec.tracks, q, limit=8)
            if results.empty:
                st.caption("Nothing matched. Try another spelling, or use a sample playlist instead.")
            for _, row in results.iterrows():
                cols = st.columns([5, 1])
                cols[0].markdown(
                    f"<div class='mono' style='font-size:0.9rem'>{row['artist_name']} · "
                    f"<b>{row['track_name']}</b></div>", unsafe_allow_html=True,
                )
                if cols[1].button("Add", key=f"add_{row['track_id']}"):
                    triple = (row['track_id'], row['artist_name'], row['track_name'])
                    if triple[0] not in [t[0] for t in st.session_state.seed_tracks]:
                        st.session_state.seed_tracks.append(triple)
        if st.session_state.seed_tracks:
            st.markdown("<div style='margin-top:1rem'><b>Your starting songs</b></div>", unsafe_allow_html=True)
            for _tid, art, title in st.session_state.seed_tracks:
                st.caption(f"·  {art} - {title}")
            if st.button("Clear songs"):
                st.session_state.seed_tracks = []
                st.rerun()
        recent = [t[0] for t in st.session_state.seed_tracks]
        pid = "cold-" + (recent[0] if recent else "")

    elif mode == "Pick a sample playlist":
        st.caption("These are real playlists from the training data. Pick one and see what fits.")
        seed_pids = list(rec.ncf.playlist_index.keys())[:50] if rec.ncf else []
        pid = st.selectbox("Sample playlist", options=[""] + seed_pids, index=1 if seed_pids else 0)
        if pid:
            in_pl = rec.tracks.merge(
                pd.DataFrame({"track_id": _seen_for(rec, pid)}), on="track_id",
            ).head(5)
            if len(in_pl):
                st.caption("First 5 songs in this playlist:")
                for _, r in in_pl.iterrows():
                    st.caption(f"·  {r['artist_name']} - {r['track_name']}")

    else:  # Paste a Spotify URL
        st.caption(
            "Heads up: Spotify recently restricted this for new developer apps. "
            "If it fails, use search instead."
        )
        url = st.text_input("Playlist URL", placeholder="https://open.spotify.com/playlist/...", label_visibility="collapsed")
        if url:
            try:
                fetched = audio.fetch_playlist_tracks(url)
                recent = [t.track_id for t in fetched]
                pid = recent[0] if recent else ""
                st.caption(f"Pulled {len(recent)} songs.")
            except audio.PlaylistAuthError as e:
                st.warning(str(e))
                return

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        model_key = st.radio(
            "Model",
            options=list(MODEL_LABELS.keys()),
            format_func=lambda k: MODEL_LABELS[k],
            horizontal=True,
            index=0,
        )
        st.caption(MODEL_HELP[model_key])
    with col2:
        k = st.slider("How many suggestions", 5, 25, 10)

    if not st.button("Recommend", type="primary"):
        return
    if not pid:
        st.warning("Add a song, pick a sample playlist, or paste a URL first.")
        return

    recs = rec.recommend(pid, recent_track_ids=recent, model=model_key, k=k)
    if not recs:
        st.error("No suggestions came back. Try adding more starting songs.")
        return

    st.markdown("<h3 style='margin-top:2rem'>Suggestions</h3>", unsafe_allow_html=True)
    for i, r in enumerate(recs, start=1):
        title = r.get("track_name") or r.get("track_id")
        artist = r.get("artist_name", "")
        cam = r.get("camelot") or ""
        tempo = r.get("tempo")
        bpm = f"{tempo:.0f} BPM" if isinstance(tempo, (int, float)) and tempo else ""
        coh = r.get("coherence")
        coh_str = f"Fits seeds: {coh:.0%}" if isinstance(coh, (int, float)) else ""
        meta = " · ".join(x for x in [cam, bpm] if x)
        st.markdown(
            f"""<div class="card rec-card">
                <div class="rec-rank">{i:02d}</div>
                <div>
                  <div class="rec-title">{title}</div>
                  <div class="rec-artist">{artist}</div>
                </div>
                <div class="rec-meta">{meta}<br/>{coh_str}</div>
              </div>""",
            unsafe_allow_html=True,
        )


@st.cache_data
def _search_mpd_vocab(tracks: pd.DataFrame, q: str, limit: int = 8) -> pd.DataFrame:
    """case-insensitive substring search across artist+title in the trained vocab."""
    if not q.strip():
        return tracks.iloc[0:0]
    needle = q.strip().lower()
    haystack = (tracks["artist_name"].fillna("").str.lower() + " " +
                tracks["track_name"].fillna("").str.lower())
    mask = haystack.str.contains(needle, regex=False, na=False)
    return tracks[mask].head(limit)


def _seen_for(rec, pid: str) -> list[str]:
    # cached preview of playlist contents; uses the saved interactions parquet
    cache = getattr(_seen_for, "_cache", None)
    if cache is None:
        try:
            interactions = pd.read_parquet(DATA_PROC / "interactions.parquet")
            cache = interactions.groupby("playlist_id")["track_id"].apply(list).to_dict()
        except FileNotFoundError:
            cache = {}
        _seen_for._cache = cache
    return cache.get(pid, [])[:5]


def _tab_why(metrics: dict):
    st.markdown("<h2>How it picks songs</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p>Every suggestion gets two scores.</p>"
        "<p>The first one is about listening patterns. The model has seen "
        "thousands of real Spotify playlists, so it knows which songs people "
        "tend to put together. If your starting songs show up alongside a lot "
        "of country music in those playlists, you'll get country recommendations.</p>"
        "<p>The second score is about whether the song actually fits musically. "
        "Are the keys compatible? Is the tempo close? Does the energy line up? "
        "It's the same kind of check a DJ runs in their head when mixing tracks live.</p>",
        unsafe_allow_html=True,
    )
    if "hybrid" in metrics:
        alpha = metrics["hybrid"].get("alpha")
        weight = int(round((1 - alpha) * 100))
        st.markdown(
            f"<p>The Music-aware model leans about <b>{weight}%</b> on the music "
            f"fit part and <b>{100 - weight}%</b> on the listening pattern. That "
            f"split was tuned on a separate slice of playlists the model never "
            f"saw during training.</p>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<p>The music-fit score is a deliberate simplification. It's not trying "
        "to capture taste, only basic compatibility. If you pick a country song "
        "as a starting point, a quiet jazz ballad will score low on fit even if "
        "people sometimes put them in the same playlist.</p>",
        unsafe_allow_html=True,
    )


def _tab_metrics(metrics: dict):
    st.markdown("<h2>How the models compare</h2>", unsafe_allow_html=True)
    comp = metrics.get("comparison")
    if not comp:
        st.info("Metrics haven't been generated yet. Run the pipeline.")
        return

    st.markdown(
        "<p>All three models were tested the same way: take 2,000 real Spotify "
        "playlists, hide the last few songs, and ask each model to predict "
        "what they were. The table below scores how well each one did. Higher "
        "is better across all columns.</p>",
        unsafe_allow_html=True,
    )

    label_map = {
        "classical": "Old-school math (the baseline)",
        "neural": "Pattern only (deep learning)",
        "hybrid": "Music-aware (deep learning + theory)",
    }
    rows = []
    for m in ("classical", "neural", "hybrid"):
        row = {"Model": label_map[m]}
        row.update({
            "Quality (top 10)": comp[m]["ndcg@10"],
            "Found in top 10": comp[m]["hit@10"],
            "Found in top 50": comp[m]["hit@50"],
            "Precision (top 10)": comp[m]["precision@10"],
            "Recall (top 50)": comp[m]["recall@50"],
        })
        rows.append(row)
    df = pd.DataFrame(rows).set_index("Model")
    # convert the two "found in" columns to percentages for nicer display
    df["Found in top 10"] = df["Found in top 10"] * 100
    df["Found in top 50"] = df["Found in top 50"] * 100
    st.dataframe(
        df,
        width="stretch",
        column_config={
            "Quality (top 10)": st.column_config.NumberColumn(
                format="%.3f",
                help="How well-ranked the correct songs are in the top 10. Industry name: NDCG@10. Higher is better.",
            ),
            "Found in top 10": st.column_config.NumberColumn(
                format="%.1f%%",
                help="Out of all the test playlists, the share where at least one correct song appeared in the top 10. Industry name: hit rate@10.",
            ),
            "Found in top 50": st.column_config.NumberColumn(
                format="%.1f%%",
                help="Same idea but checking the top 50.",
            ),
            "Precision (top 10)": st.column_config.NumberColumn(
                format="%.3f",
                help="Of the 10 suggestions, what fraction were actually correct.",
            ),
            "Recall (top 50)": st.column_config.NumberColumn(
                format="%.3f",
                help="Of all the correct songs we were looking for, what fraction the top 50 actually found.",
            ),
        },
    )

    st.markdown(
        "<p>The old-school math model wins on every metric. Counterintuitive, "
        "but a known result in this kind of work. Matrix factorization is a "
        "very strong baseline. Beating it would take a lot more training time "
        "than this project had, plus access to better music data than what's "
        "free on Kaggle. Both are honest limitations and they're written up in "
        "the README.</p>",
        unsafe_allow_html=True,
    )

    img = RESULTS_F / "comparison.png"
    if img.exists():
        st.image(str(img), width="stretch")
    st.caption(
        f"Tested on {comp.get('eval_playlists', '?'):,} held-out playlists. "
        f"Music features were available for {comp.get('audio_feature_match_rate', 0):.0%} of songs."
    )


def _tab_theory():
    st.markdown("<h2>The music theory bit</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p>DJs use a tool called the Camelot wheel to figure out which songs "
        "will mix smoothly together. Every musical key gets a code (1-12) and "
        "a letter (A for minor, B for major). Keys next to each other on the "
        "wheel share most of their notes, so songs in those keys blend well. "
        "Songs from opposite sides of the wheel clash.</p>"
        "<p>The Music-aware model uses this exact idea when scoring suggestions. "
        "It checks whether a candidate song's key is close to your starting "
        "songs' keys on the wheel.</p>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([3, 2])
    with col1:
        fig = camelot.draw(
            track_codes=["8B", "9B", "10B", "5A", "12A"],
            highlight="8B",
            title="Example: songs in C, G, and D major, plus two minors",
        )
        st.pyplot(fig, clear_figure=True)
    with col2:
        st.markdown(
            "<p>The gold star is your starting song's key. "
            "Burgundy dots are candidate songs the model is considering. "
            "Anything right next to the star will sound smooth; anything "
            "across the wheel will clash.</p>",
            unsafe_allow_html=True,
        )


def _tab_methodology(metrics: dict):
    st.markdown("<h2>How this was built</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <p>The training data is 20,000 real Spotify playlists pulled from
        their Million Playlist Dataset (released for research). Playlists
        run from 5 songs to a few hundred. For testing, the last 20% of each
        playlist gets hidden and the model has to guess what was there.</p>

        <p>For the music-theory side, Spotify used to give out per-song info
        like tempo, key, and energy through a free API. They shut that off
        for new developer apps in late 2024, which is annoying but also the
        reality. This project pulls those features from a Kaggle dataset
        instead. It only covers about 2% of the playlist songs, which is why
        the music-aware model doesn't pull ahead by more than it does.</p>

        <p>All three models were scored on the same 2,000 held-out playlists
        with the same five metrics. None of them got hidden from the
        comparison table when their numbers came in lower than expected.</p>
        """,
        unsafe_allow_html=True,
    )
    if "match_rate" in metrics:
        mr = metrics["match_rate"]
        st.markdown(
            f"<p class='mono'>Music feature coverage: "
            f"{mr['matched']:,} of {mr['total_mpd_tracks']:,} songs "
            f"({mr['match_rate']:.1%}).</p>",
            unsafe_allow_html=True,
        )


def _tab_about():
    st.markdown("<h2>About</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <p>Built by Johnny Nguyen. Source code, training scripts, and a
        longer write-up live on
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
        "Try it", "How it picks", "Compare models",
        "Music theory", "How it was built", "About",
    ])
    with tabs[0]: _tab_try(rec)
    with tabs[1]: _tab_why(metrics)
    with tabs[2]: _tab_metrics(metrics)
    with tabs[3]: _tab_theory()
    with tabs[4]: _tab_methodology(metrics)
    with tabs[5]: _tab_about()


if __name__ == "__main__":
    main()
