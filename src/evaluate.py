"""ranking metrics for top-K recommendation.

every function takes ``recommendations`` (a list-of-lists or array of track
ids, one row per playlist) and ``ground_truth`` (set per playlist), plus k.
returning the mean over playlists so model comparison is one number each.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np


def _truncate(recs: Sequence, k: int) -> list:
    return list(recs)[:k]


def hit_rate_at_k(recommendations: Sequence[Sequence], truths: Sequence[Iterable], k: int) -> float:
    hits = 0
    n = 0
    for recs, gt in zip(recommendations, truths, strict=False):
        gt_set = set(gt)
        if not gt_set:
            continue
        n += 1
        if any(item in gt_set for item in _truncate(recs, k)):
            hits += 1
    return hits / n if n else 0.0


def precision_at_k(recommendations: Sequence[Sequence], truths: Sequence[Iterable], k: int) -> float:
    scores = []
    for recs, gt in zip(recommendations, truths, strict=False):
        gt_set = set(gt)
        if not gt_set:
            continue
        top = _truncate(recs, k)
        if not top:
            scores.append(0.0)
            continue
        scores.append(sum(1 for x in top if x in gt_set) / len(top))
    return float(np.mean(scores)) if scores else 0.0


def recall_at_k(recommendations: Sequence[Sequence], truths: Sequence[Iterable], k: int) -> float:
    scores = []
    for recs, gt in zip(recommendations, truths, strict=False):
        gt_set = set(gt)
        if not gt_set:
            continue
        top = _truncate(recs, k)
        scores.append(sum(1 for x in top if x in gt_set) / len(gt_set))
    return float(np.mean(scores)) if scores else 0.0


def ndcg_at_k(recommendations: Sequence[Sequence], truths: Sequence[Iterable], k: int) -> float:
    scores = []
    for recs, gt in zip(recommendations, truths, strict=False):
        gt_set = set(gt)
        if not gt_set:
            continue
        top = _truncate(recs, k)
        dcg = 0.0
        for i, item in enumerate(top):
            if item in gt_set:
                dcg += 1.0 / np.log2(i + 2)
        ideal_n = min(len(gt_set), k)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_n))
        scores.append(dcg / idcg if idcg > 0 else 0.0)
    return float(np.mean(scores)) if scores else 0.0


def evaluate_all(
    recommendations: Sequence[Sequence],
    truths: Sequence[Iterable],
    ks: Sequence[int] = (10, 50),
) -> dict[str, float]:
    """one-call wrapper used by every notebook: returns ndcg, hit, prec, recall at each k."""
    out: dict[str, float] = {}
    for k in ks:
        out[f"ndcg@{k}"] = ndcg_at_k(recommendations, truths, k)
        out[f"hit@{k}"] = hit_rate_at_k(recommendations, truths, k)
        out[f"precision@{k}"] = precision_at_k(recommendations, truths, k)
        out[f"recall@{k}"] = recall_at_k(recommendations, truths, k)
    return out
