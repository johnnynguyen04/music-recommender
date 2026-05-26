"""generate the 7 narrative notebooks from a single source of truth.

each notebook is a thin walk-through: markdown explaining what + why, then
code that loads precomputed artifacts (or recomputes on a small subset). the
heavy training happens in scripts/run_pipeline.py; these are for reading.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"


def md(*lines: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": [s + "\n" for s in lines]}


def code(*lines: str) -> dict:
    return {
        "cell_type": "code", "metadata": {}, "execution_count": None,
        "outputs": [], "source": [s + "\n" for s in lines],
    }


def nb(*cells) -> dict:
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
        },
        "cells": list(cells),
    }


def write(name: str, notebook: dict) -> None:
    NB.mkdir(exist_ok=True)
    (NB / name).write_text(json.dumps(notebook, indent=1))
    print(f"wrote {name}")


SETUP = code(
    "import sys, json",
    "from pathlib import Path",
    "ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()",
    "sys.path.insert(0, str(ROOT))",
    "import pandas as pd, numpy as np, matplotlib.pyplot as plt",
)


def nb01() -> dict:
    return nb(
        md("# 01 · data exploration",
           "",
           "the spotify million playlist dataset (MPD) ships as 1000 JSON slice files, "
           "1000 playlists each. for development i load the first 20 slices "
           "(20k playlists, ~1.3M interactions, ~260k unique tracks) so the loop "
           "from raw json to a trained model fits in a few minutes."),
        SETUP,
        code("from src.data import load_dataset",
             "ds = load_dataset(source='mpd', cache_dir=ROOT/'data/processed',",
             "                  slice_dir=str(ROOT/'data/raw'), rebuild=False)",
             "print(f'playlists: {ds.n_playlists():,}')",
             "print(f'unique tracks: {ds.n_tracks():,}')",
             "print(f'interactions: {len(ds.interactions):,}')"),
        md("## playlist length distribution"),
        code("pl_len = ds.interactions.groupby('playlist_id').size()",
             "fig, ax = plt.subplots(figsize=(7, 3.5))",
             "ax.hist(pl_len, bins=50, color='#8b3a3a', alpha=0.85)",
             "ax.set_xlabel('tracks per playlist'); ax.set_ylabel('playlists')",
             "ax.set_title('playlist length distribution'); plt.show()"),
        md("## track popularity (long tail as expected)"),
        code("track_pop = ds.interactions.groupby('track_id').size().sort_values(ascending=False)",
             "fig, ax = plt.subplots(figsize=(7, 3.5))",
             "ax.plot(track_pop.values[:5000], color='#1f1c1a')",
             "ax.set_xlabel('track rank'); ax.set_ylabel('# playlists containing track')",
             "ax.set_yscale('log'); ax.set_title('track popularity (top 5000)')",
             "plt.show()"),
        md("the top-1% of tracks dominate the playlist appearances by orders of "
           "magnitude. classical CF will lean on that signal; the hybrid model "
           "should help most on tracks in the mid-tail where collaborative "
           "evidence is sparse."),
    )


def nb02() -> dict:
    return nb(
        md("# 02 · classical CF baseline (implicit ALS)",
           "",
           "alternating least squares on the playlist-track confidence matrix. "
           "this is the reference both other models have to beat. "
           "metrics come from `results/metrics/classical.json`, written by "
           "`scripts/run_pipeline.py`."),
        SETUP,
        code("m = json.loads((ROOT/'results/metrics/classical.json').read_text())",
             "print(json.dumps({k: v for k, v in m.items() if '@' in k}, indent=2))"),
        md("ALS treats every observation as confident-positive scaled by alpha and "
           "every non-observation as a soft negative. that is reasonable for "
           "playlists since the absence of a track usually means the curator "
           "didn't pick it, not that they disliked it."),
        md("### what this baseline tells us",
           "",
           "head-of-distribution accuracy is decent because the popular tracks "
           "co-occur often enough for ALS to learn good factors. accuracy on the "
           "tail is the gap the neural and hybrid models try to close."),
    )


def nb03() -> dict:
    return nb(
        md("# 03 · neural collaborative filtering",
           "",
           "two-tower architecture: separate embedding tables for playlists and "
           "tracks, dot product as the score, BPR pairwise loss with 4 random "
           "negatives per positive. trained in `scripts/run_pipeline.py`; this "
           "notebook just reads the artifact."),
        SETUP,
        code("from src import neural",
             "m = json.loads((ROOT/'results/metrics/neural.json').read_text())",
             "print(json.dumps({k: v for k, v in m.items() if '@' in k}, indent=2))",
             "history = m.get('train_loss_history', [])",
             "if history:",
             "    fig, ax = plt.subplots(figsize=(6, 3))",
             "    ax.plot(range(1, len(history) + 1), history, marker='o', color='#1f1c1a')",
             "    ax.set_xlabel('epoch'); ax.set_ylabel('BPR loss'); plt.show()"),
        md("### vs the baseline",
           "",
           "the neural model's edge over ALS is usually small at K=10 on a "
           "playlist-completion task; both rely on the same co-occurrence signal "
           "and ALS is a strong baseline. the win is on cold or low-evidence "
           "playlists, which is where the hybrid layer adds the most value too."),
    )


def nb04() -> dict:
    return nb(
        md("# 04 · audio features join",
           "",
           "spotify deprecated `/audio-features` for new developer apps in late "
           "2024. instead i join MPD track ids to a pre-fetched kaggle dataset "
           "(`maharshipandya/-spotify-tracks-dataset`, ~114k tracks). a small "
           "fuzzy fallback covers a sample of unmatched titles."),
        SETUP,
        code("m = json.loads((ROOT/'results/metrics/match_rate.json').read_text())",
             "print(json.dumps(m, indent=2))"),
        code("joined = pd.read_parquet(ROOT/'data/processed/audio_features_joined.parquet')",
             "fig, axes = plt.subplots(1, 3, figsize=(11, 3))",
             "for ax, col in zip(axes, ['tempo', 'energy', 'valence']):",
             "    ax.hist(joined[col].dropna(), bins=40, color='#b8924a', alpha=0.85)",
             "    ax.set_title(col)",
             "plt.tight_layout(); plt.show()"),
        md("### honest note on coverage",
           "",
           "the kaggle dataset is genre-stratified, not popularity-stratified, "
           "so direct-id match rate is modest. the hybrid model has to gracefully "
           "fall through to a neutral coherence score for unmatched tracks; we "
           "report match rate explicitly in the README so the number isn't "
           "hidden."),
    )


def nb05() -> dict:
    return nb(
        md("# 05 · hybrid model and alpha sweep",
           "",
           "final score is `alpha · cf + (1-alpha) · theory`. we re-rank the "
           "top-200 CF candidates by their average coherence with the last few "
           "tracks in the playlist. alpha is grid-searched on a held-out "
           "validation split using NDCG@10."),
        SETUP,
        code("m = json.loads((ROOT/'results/metrics/hybrid.json').read_text())",
             "print(json.dumps({k: v for k, v in m.items() if '@' in k or k == 'alpha'}, indent=2))"),
        code("sweep = m['alpha_sweep_val_ndcg10']",
             "xs = sorted(float(k) for k in sweep)",
             "ys = [sweep[str(x)] for x in xs]",
             "fig, ax = plt.subplots(figsize=(6, 3.5))",
             "ax.plot(xs, ys, marker='o', color='#8b3a3a')",
             "ax.axvline(m['alpha'], color='#1f1c1a', linestyle='--', alpha=0.4,",
             "           label=f'best α = {m[\"alpha\"]}')",
             "ax.set_xlabel('alpha (weight on CF)'); ax.set_ylabel('val NDCG@10')",
             "ax.legend(); plt.show()"),
        md("the alpha sweep is the single most informative plot in this project. "
           "if the curve peaks at alpha = 1.0, the theory features didn't help. "
           "if it peaks below 1.0, the theory features are pulling weight."),
    )


def nb06() -> dict:
    return nb(
        md("# 06 · music theory features explained",
           "",
           "this is the unique angle. three features derived per track:",
           "",
           "1. **Camelot code** from `key` and `mode` (DJ-standard harmonic mixing wheel)",
           "2. **harmonic distance** between two tracks (0 = same key, larger = jarrier)",
           "3. **tempo and energy compatibility** (1.0 means matched, 0.0 means jarring)"),
        SETUP,
        code("from src.theory import camelot_code, harmonic_distance, tempo_compatibility, coherence_score, TrackFeatures"),
        md("### worked example",
           "C major and A minor share all seven scale degrees (relative major / "
           "minor). on the wheel they're 8B and 8A. a transition between them "
           "should feel smooth; F# major (2B) is on the opposite face and will "
           "feel jarring without preparation."),
        code("print('C major   ->', camelot_code(0, 1))",
             "print('A minor   ->', camelot_code(9, 0))",
             "print('F# major  ->', camelot_code(6, 1))",
             "print()",
             "print('harmonic distance C maj -> A min :', harmonic_distance('8B', '8A'))",
             "print('harmonic distance C maj -> G maj :', harmonic_distance('8B', '9B'))",
             "print('harmonic distance C maj -> F# maj:', harmonic_distance('8B', '2B'))"),
        md("### tempo compatibility curve"),
        code("import numpy as np",
             "deltas = np.linspace(0, 50, 200)",
             "ys = [tempo_compatibility(120, 120 + d) for d in deltas]",
             "fig, ax = plt.subplots(figsize=(6, 3))",
             "ax.plot(deltas, ys, color='#1f1c1a')",
             "ax.set_xlabel('BPM gap from seed'); ax.set_ylabel('tempo compatibility')",
             "plt.show()"),
        md("### combined coherence score"),
        code("seed = TrackFeatures('seed', '8B', 120, 0.7, 0.5, 0.6, 0.2)",
             "for cand_code, bpm, energy in [('8B', 120, 0.7), ('8A', 122, 0.65),",
             "                                ('9B', 124, 0.7), ('2B', 95, 0.3)]:",
             "    cand = TrackFeatures('c', cand_code, bpm, energy, 0.5, 0.6, 0.2)",
             "    print(f'{cand_code} {bpm}bpm e={energy} -> {coherence_score(seed, cand):.3f}')"),
        md("the coherence score is a deliberately simple weighted sum so the UI "
           "can show users a per-recommendation breakdown without having to "
           "explain a black box."),
    )


def nb07() -> dict:
    return nb(
        md("# 07 · side-by-side comparison",
           "",
           "everything trained and evaluated on the same playlists. nothing is "
           "dropped from this table. null findings live here too."),
        SETUP,
        code("comp = json.loads((ROOT/'results/metrics/comparison.json').read_text())",
             "rows = []",
             "for model in ('classical', 'neural', 'hybrid'):",
             "    row = {'model': model}; row.update(comp[model]); rows.append(row)",
             "df = pd.DataFrame(rows).set_index('model')",
             "df.style.format('{:.4f}')"),
        code("img_path = ROOT/'results/figures/comparison.png'",
             "if img_path.exists():",
             "    from IPython.display import Image; Image(str(img_path))"),
        md("### honest interpretation",
           "",
           "look at the alpha value reported in `hybrid.json`. if it's close to "
           "1.0, the music-theory features didn't add much on this evaluation. "
           "if it's lower, they pulled rank. either result is a real finding for "
           "an undergrad portfolio project: showing the comparison and saying "
           "'this is what i measured' is better than hiding the negative case."),
        md("### where the hybrid is most likely to help",
           "",
           "stylistically narrow playlists (a single mood, similar tempo). it "
           "is likely to **hurt** on highly eclectic playlists where the user "
           "intentionally jumps between styles."),
    )


if __name__ == "__main__":
    write("01_data_exploration.ipynb", nb01())
    write("02_classical_cf_baseline.ipynb", nb02())
    write("03_neural_cf.ipynb", nb03())
    write("04_audio_features_join.ipynb", nb04())
    write("05_hybrid_model.ipynb", nb05())
    write("06_theory_features.ipynb", nb06())
    write("07_results_comparison.ipynb", nb07())
