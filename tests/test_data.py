import pandas as pd

from src.data import build_matrix, split_holdout


def _toy_interactions():
    rows = []
    for pid in ("p1", "p2", "p3"):
        for pos, t in enumerate(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10"]):
            rows.append((pid, t, pos))
    return pd.DataFrame(rows, columns=["playlist_id", "track_id", "pos"])


def test_split_holdout_leaves_tail_in_test():
    df = _toy_interactions()
    splits = split_holdout(df, holdout_frac=0.2)
    # 10 tracks each, 20% holdout -> last 2 in test for every playlist
    for pid in df["playlist_id"].unique():
        train = splits.train[splits.train["playlist_id"] == pid]["track_id"].tolist()
        test = splits.test[splits.test["playlist_id"] == pid]["track_id"].tolist()
        assert test == ["t9", "t10"]
        assert "t9" not in train and "t10" not in train


def test_split_holdout_short_playlist_stays_in_train():
    rows = [("short", "x", 0), ("short", "y", 1), ("short", "z", 2)]
    df = pd.DataFrame(rows, columns=["playlist_id", "track_id", "pos"])
    splits = split_holdout(df, holdout_frac=0.2, min_train=5)
    assert len(splits.test) == 0
    assert len(splits.train) == 3


def test_build_matrix_shape_and_density():
    df = _toy_interactions()
    mat, pi, ti = build_matrix(df)
    assert mat.shape == (3, 10)
    assert mat.nnz == 30
    assert set(pi.keys()) == {"p1", "p2", "p3"}
    assert set(ti.keys()) == {f"t{i}" for i in range(1, 11)}
