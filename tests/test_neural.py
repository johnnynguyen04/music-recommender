import numpy as np
import torch

from src.neural import TwoTowerCF, TwoTowerConfig, fit, recommend


def test_forward_pass_shapes():
    model = TwoTowerCF(n_playlists=10, n_tracks=20, embed_dim=8)
    p = torch.tensor([0, 1, 2])
    pos = torch.tensor([3, 4, 5])
    neg = torch.tensor([[6, 7], [8, 9], [10, 11]])
    loss = model(p, pos, neg)
    assert loss.shape == ()
    assert loss.item() > 0


def test_tiny_training_smoke():
    rng = np.random.default_rng(0)
    n_p, n_t = 30, 100
    n_inter = 600
    p_idx = rng.integers(0, n_p, size=n_inter)
    t_idx = rng.integers(0, n_t, size=n_inter)
    p_index = {f"p{i}": i for i in range(n_p)}
    t_index = {f"t{i}": i for i in range(n_t)}
    cfg = TwoTowerConfig(n_playlists=n_p, n_tracks=n_t, embed_dim=8, epochs=1, batch_size=64)
    trained = fit(p_idx, t_idx, p_index, t_index, cfg=cfg)
    recs = recommend(trained, ["p0", "p1"], k=5)
    assert len(recs) == 2
    assert len(recs[0]) == 5
