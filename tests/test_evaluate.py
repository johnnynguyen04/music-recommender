from src.evaluate import (
    evaluate_all,
    hit_rate_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_hit_rate_perfect():
    recs = [["a", "b", "c"]]
    truths = [{"b"}]
    assert hit_rate_at_k(recs, truths, k=3) == 1.0


def test_hit_rate_miss():
    recs = [["a", "b", "c"]]
    truths = [{"z"}]
    assert hit_rate_at_k(recs, truths, k=3) == 0.0


def test_ndcg_first_position_is_one():
    recs = [["a", "b", "c"]]
    truths = [{"a"}]
    assert ndcg_at_k(recs, truths, k=3) == 1.0


def test_precision_recall_basic():
    recs = [["a", "b", "c", "d"]]
    truths = [{"a", "c"}]
    assert precision_at_k(recs, truths, k=4) == 0.5
    assert recall_at_k(recs, truths, k=4) == 1.0


def test_evaluate_all_returns_expected_keys():
    recs = [["a", "b", "c"]]
    truths = [{"a"}]
    out = evaluate_all(recs, truths, ks=(1, 3))
    assert set(out.keys()) == {
        "ndcg@1", "hit@1", "precision@1", "recall@1",
        "ndcg@3", "hit@3", "precision@3", "recall@3",
    }
