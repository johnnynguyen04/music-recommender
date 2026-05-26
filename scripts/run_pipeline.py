"""end-to-end training pipeline: data -> classical -> neural -> hybrid.

writes:
  data/processed/interactions.parquet, tracks.parquet
  data/processed/audio_features_joined.parquet
  results/metrics/{classical,neural,hybrid}.json
  results/metrics/comparison.json
  results/metrics/match_rate.json
  results/figures/comparison.png, alpha_sweep.png
  artifacts/ncf.pt

run with:
  uv run python scripts/run_pipeline.py
"""

from __future__ import annotations

import os
# pin BLAS threads BEFORE numpy / scipy / implicit import.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import classical, hybrid, neural  # noqa: E402
from src.data import build_matrix, load_dataset, split_holdout  # noqa: E402
from src.evaluate import evaluate_all, ndcg_at_k  # noqa: E402
from src.theory import features_from_row  # noqa: E402

DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
DATA_AUDIO = ROOT / "data" / "audio_features" / "dataset.csv"
RESULTS_M = ROOT / "results" / "metrics"
RESULTS_F = ROOT / "results" / "figures"
ARTIFACTS = ROOT / "artifacts"

EVAL_SAMPLE = 2000   # cap eval playlists for speed; documented in README
KS = (10, 50)


def step(name: str) -> float:
    print(f"\n=== {name} ===")
    return time.time()


def stamp(t0: float):
    print(f"   ({time.time() - t0:.1f}s)")


def main():
    DATA_PROC.mkdir(parents=True, exist_ok=True)
    RESULTS_M.mkdir(parents=True, exist_ok=True)
    RESULTS_F.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    t = step("load mpd slices into normalized dataset")
    ds = load_dataset(source="mpd", cache_dir=DATA_PROC, slice_dir=str(DATA_RAW), rebuild=False)
    print(f"   playlists={ds.n_playlists():,}  unique tracks={ds.n_tracks():,}  "
          f"interactions={len(ds.interactions):,}")
    stamp(t)

    t = step("per-playlist holdout split (last 20% -> half val, half test)")
    splits = split_holdout(ds.interactions, holdout_frac=0.2)
    rng = np.random.default_rng(7)
    test_pids = splits.test["playlist_id"].unique()
    perm = rng.permutation(len(test_pids))
    half = len(perm) // 2
    val_pids = set(test_pids[perm[:half]])
    test_pids_only = set(test_pids[perm[half:]])
    val = splits.test[splits.test["playlist_id"].isin(val_pids)].copy()
    tst = splits.test[splits.test["playlist_id"].isin(test_pids_only)].copy()
    train = splits.train
    print(f"   train interactions={len(train):,}  val={len(val):,}  test={len(tst):,}")
    stamp(t)

    t = step("build sparse train matrix")
    train_mat, p_idx, t_idx = build_matrix(train)
    print(f"   matrix shape={train_mat.shape}  nnz={train_mat.nnz:,}")
    stamp(t)

    # sample eval playlists once so all three models score on the same set
    eval_test_pids = _sample_eval(tst, p_idx, EVAL_SAMPLE, seed=11)
    eval_val_pids = _sample_eval(val, p_idx, EVAL_SAMPLE // 2, seed=13)
    test_truth = _truth(tst, eval_test_pids)
    val_truth = _truth(val, eval_val_pids)
    print(f"   eval test playlists={len(eval_test_pids):,}  eval val={len(eval_val_pids):,}")

    t = step("train classical ALS baseline")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    try:
        cf = classical.fit_als(train_mat, p_idx, t_idx, factors=64, iterations=15)
        backend = "als"
    except Exception as e:
        print(f"   als failed ({e!r}); falling back to TruncatedSVD")
        cf = classical.fit_svd(train_mat, p_idx, t_idx, factors=64)
        backend = "svd"
    cf_recs_test = classical.recommend(cf, train_mat, eval_test_pids, k=max(KS))
    cf_metrics = evaluate_all(cf_recs_test, test_truth, ks=KS)
    cf_metrics["backend"] = backend
    _write_json(RESULTS_M / "classical.json", cf_metrics)
    print(f"   classical: {_fmt(cf_metrics)}")
    stamp(t)

    t = step("train neural two-tower CF")
    pi_arr = train["playlist_id"].map(p_idx).to_numpy()
    ti_arr = train["track_id"].map(t_idx).to_numpy()
    cfg = neural.TwoTowerConfig(
        n_playlists=len(p_idx),
        n_tracks=len(t_idx),
        embed_dim=64,
        epochs=4,
        batch_size=8192,
        lr=5e-3,
    )
    trained = neural.fit(pi_arr.astype(np.int64), ti_arr.astype(np.int64), p_idx, t_idx, cfg=cfg)
    neural.save(trained, ARTIFACTS / "ncf.pt")
    seen_per_pl = _build_seen(train, eval_test_pids)
    ncf_recs_test = neural.recommend(trained, eval_test_pids, seen_per_playlist=seen_per_pl, k=max(KS))
    ncf_metrics = evaluate_all(ncf_recs_test, test_truth, ks=KS)
    ncf_metrics["train_loss_history"] = trained.history
    _write_json(RESULTS_M / "neural.json", ncf_metrics)
    print(f"   neural:    {_fmt(ncf_metrics)}")
    stamp(t)

    t = step("join mpd tracks to kaggle audio features")
    feats_df, match_stats = _join_audio_features(ds.tracks, DATA_AUDIO)
    feats_df.to_parquet(DATA_PROC / "audio_features_joined.parquet", index=False)
    _write_json(RESULTS_M / "match_rate.json", match_stats)
    print(f"   audio features match rate: {match_stats['match_rate']:.1%} "
          f"({match_stats['matched']:,}/{match_stats['total_mpd_tracks']:,} mpd tracks)")
    stamp(t)

    t = step("tune hybrid alpha on val set")
    features_by_id = {r["track_id"]: features_from_row(r) for _, r in feats_df.iterrows()
                      if r.get("track_id")}
    seed_per_pl_val = _build_seed_tracks(train, eval_val_pids)
    seen_per_pl_val = _build_seen(train, eval_val_pids)
    best_alpha, alpha_scores = hybrid.tune_alpha(
        trained, eval_val_pids, [set(val_truth[i]) for i in range(len(val_truth))],
        seed_per_pl_val, features_by_id, seen_per_pl_val, ndcg_at_k, k=10,
    )
    print(f"   best alpha (val ndcg@10): {best_alpha}  sweep={alpha_scores}")
    stamp(t)

    t = step("evaluate hybrid on test")
    seed_per_pl_test = _build_seed_tracks(train, eval_test_pids)
    hyb_recs = hybrid.recommend(
        trained, eval_test_pids, seed_per_pl_test, features_by_id,
        seen_per_playlist=seen_per_pl, cfg=hybrid.HybridConfig(alpha=best_alpha), k=max(KS),
    )
    hyb_metrics = evaluate_all(hyb_recs, test_truth, ks=KS)
    hyb_metrics["alpha"] = best_alpha
    hyb_metrics["alpha_sweep_val_ndcg10"] = {str(k): v for k, v in alpha_scores.items()}
    _write_json(RESULTS_M / "hybrid.json", hyb_metrics)
    print(f"   hybrid:    {_fmt(hyb_metrics)}")
    stamp(t)

    comparison = {
        "eval_playlists": len(eval_test_pids),
        "classical": {k: cf_metrics[k] for k in cf_metrics if "@" in k},
        "neural": {k: ncf_metrics[k] for k in ncf_metrics if "@" in k},
        "hybrid": {k: hyb_metrics[k] for k in hyb_metrics if "@" in k},
        "alpha": best_alpha,
        "audio_feature_match_rate": match_stats["match_rate"],
    }
    _write_json(RESULTS_M / "comparison.json", comparison)
    _plot_comparison(comparison, RESULTS_F / "comparison.png")
    _plot_alpha_sweep(alpha_scores, RESULTS_F / "alpha_sweep.png")
    print("\n=== done ===")
    print(json.dumps(comparison, indent=2))


def _sample_eval(df: pd.DataFrame, p_idx: dict, n: int, seed: int) -> list[str]:
    valid = [p for p in df["playlist_id"].unique() if p in p_idx]
    rng = np.random.default_rng(seed)
    n = min(n, len(valid))
    return list(rng.choice(valid, size=n, replace=False))


def _truth(test_df: pd.DataFrame, pids: list[str]) -> list[set[str]]:
    by_pid = test_df.groupby("playlist_id")["track_id"].apply(set).to_dict()
    return [by_pid.get(p, set()) for p in pids]


def _build_seen(train_df: pd.DataFrame, pids: list[str]) -> dict[str, set[str]]:
    sub = train_df[train_df["playlist_id"].isin(set(pids))]
    return sub.groupby("playlist_id")["track_id"].apply(set).to_dict()


def _build_seed_tracks(train_df: pd.DataFrame, pids: list[str], tail: int = 5) -> dict[str, list[str]]:
    sub = train_df[train_df["playlist_id"].isin(set(pids))].sort_values(["playlist_id", "pos"])
    out: dict[str, list[str]] = {}
    for pid, g in sub.groupby("playlist_id"):
        out[pid] = g["track_id"].tolist()[-tail:]
    return out


def _join_audio_features(mpd_tracks: pd.DataFrame, csv_path: Path) -> tuple[pd.DataFrame, dict]:
    feats = pd.read_csv(csv_path)
    feats["track_id"] = feats["track_id"].astype(str)
    direct = feats.merge(
        mpd_tracks[["track_id", "track_name", "artist_name"]],
        on="track_id", how="inner", suffixes=("", "_mpd"),
    )
    matched_ids = set(direct["track_id"].astype(str))
    unmatched = mpd_tracks[~mpd_tracks["track_id"].astype(str).isin(matched_ids)].copy()

    # cheap fuzzy fallback only on a small sample so the pipeline stays fast;
    # documented in the readme limitations section.
    sample = unmatched.head(3000).copy()
    fuzzy_rows = []
    feats["search_key"] = (feats["track_name"].fillna("") + " - " +
                           feats["artists"].fillna("").str.split(";").str[0])
    keys = feats["search_key"].tolist()
    keys_idx = {k: i for i, k in enumerate(keys)}
    for _, row in sample.iterrows():
        q = f"{row['track_name']} - {row['artist_name']}"
        best = process.extractOne(q, keys, scorer=fuzz.WRatio, score_cutoff=92)
        if best is None:
            continue
        i = keys_idx[best[0]]
        fr = feats.iloc[i].to_dict()
        fr["track_id"] = row["track_id"]
        fuzzy_rows.append(fr)
    fuzzy = pd.DataFrame(fuzzy_rows)
    joined = pd.concat([direct, fuzzy], ignore_index=True)
    joined = joined.drop_duplicates(subset=["track_id"])

    total = len(mpd_tracks)
    stats = {
        "total_mpd_tracks": int(total),
        "direct_id_matches": int(len(direct)),
        "fuzzy_matches": int(len(fuzzy)),
        "matched": int(len(joined)),
        "match_rate": float(len(joined) / total) if total else 0.0,
        "fuzzy_sample_size": int(len(sample)),
    }
    return joined, stats


def _fmt(m: dict) -> str:
    return " ".join(f"{k}={v:.4f}" for k, v in m.items() if isinstance(v, float) and "@" in k)


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2))


def _plot_comparison(comp: dict, out: Path) -> None:
    metrics = [k for k in comp["classical"].keys()]
    models = ["classical", "neural", "hybrid"]
    width = 0.27
    x = np.arange(len(metrics))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, m in enumerate(models):
        vals = [comp[m][k] for k in metrics]
        ax.bar(x + (i - 1) * width, vals, width, label=m)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, rotation=20)
    ax.set_ylabel("score")
    ax.set_title("three-tier comparison on held-out test playlists")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def _plot_alpha_sweep(scores: dict, out: Path) -> None:
    items = sorted(scores.items())
    xs = [a for a, _ in items]
    ys = [s for _, s in items]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xs, ys, marker="o")
    ax.set_xlabel("alpha (weight on CF)")
    ax.set_ylabel("val ndcg@10")
    ax.set_title("hybrid alpha sweep")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
