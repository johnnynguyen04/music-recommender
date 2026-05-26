"""two-tower neural collaborative filter in PyTorch.

design choices:
  - separate embedding tables for playlists and tracks
  - score(playlist, track) = dot(emb_p, emb_t)
  - BPR pairwise loss with random negative sampling
  - CPU-friendly defaults; bump batch_size and embed_dim if a GPU is around

trains fast on the dev-size MPD subset (50k playlists, ~1M interactions). for
the full 1M-playlist run, halve embed_dim or chunk the training set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


@dataclass
class TwoTowerConfig:
    n_playlists: int
    n_tracks: int
    embed_dim: int = 64
    n_neg: int = 4
    lr: float = 5e-3
    weight_decay: float = 1e-6
    batch_size: int = 4096
    epochs: int = 5
    seed: int = 7


class TwoTowerCF(nn.Module):
    def __init__(self, n_playlists: int, n_tracks: int, embed_dim: int = 64):
        super().__init__()
        self.playlist_emb = nn.Embedding(n_playlists, embed_dim)
        self.track_emb = nn.Embedding(n_tracks, embed_dim)
        nn.init.normal_(self.playlist_emb.weight, std=0.01)
        nn.init.normal_(self.track_emb.weight, std=0.01)

    def score(self, playlist_idx: torch.Tensor, track_idx: torch.Tensor) -> torch.Tensor:
        p = self.playlist_emb(playlist_idx)
        t = self.track_emb(track_idx)
        return (p * t).sum(dim=-1)

    def forward(self, p: torch.Tensor, pos: torch.Tensor, neg: torch.Tensor) -> torch.Tensor:
        # pos: (B,), neg: (B, n_neg). returns BPR loss.
        p_emb = self.playlist_emb(p)                  # (B, D)
        pos_emb = self.track_emb(pos)                 # (B, D)
        neg_emb = self.track_emb(neg)                 # (B, n_neg, D)
        pos_score = (p_emb * pos_emb).sum(dim=-1)     # (B,)
        neg_score = (p_emb.unsqueeze(1) * neg_emb).sum(dim=-1)  # (B, n_neg)
        diff = pos_score.unsqueeze(1) - neg_score
        return -torch.log(torch.sigmoid(diff) + 1e-12).mean()


class _BPRDataset(Dataset):
    def __init__(self, playlist_idx: np.ndarray, track_idx: np.ndarray, n_tracks: int, n_neg: int, seen: dict[int, set[int]], seed: int):
        self.p = playlist_idx
        self.t = track_idx
        self.n_tracks = n_tracks
        self.n_neg = n_neg
        self.seen = seen
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.p)

    def __getitem__(self, i: int):
        p = int(self.p[i])
        pos = int(self.t[i])
        negs = np.empty(self.n_neg, dtype=np.int64)
        seen = self.seen.get(p, set())
        for k in range(self.n_neg):
            while True:
                candidate = int(self.rng.integers(0, self.n_tracks))
                if candidate not in seen:
                    break
            negs[k] = candidate
        return p, pos, negs


@dataclass
class TrainedNCF:
    model: TwoTowerCF
    config: TwoTowerConfig
    playlist_index: dict[str, int]
    track_index: dict[str, int]
    history: list[float] = field(default_factory=list)

    def reverse_track_index(self) -> list[str]:
        ids = [""] * len(self.track_index)
        for tid, i in self.track_index.items():
            ids[i] = tid
        return ids


def fit(
    playlist_idx: np.ndarray,
    track_idx: np.ndarray,
    playlist_index: dict[str, int],
    track_index: dict[str, int],
    cfg: TwoTowerConfig | None = None,
    device: str | None = None,
) -> TrainedNCF:
    """train a two-tower model on (playlist, track) positive pairs."""
    if cfg is None:
        cfg = TwoTowerConfig(n_playlists=len(playlist_index), n_tracks=len(track_index))
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    seen: dict[int, set[int]] = {}
    for p, t in zip(playlist_idx, track_idx, strict=False):
        seen.setdefault(int(p), set()).add(int(t))

    ds = _BPRDataset(playlist_idx, track_idx, cfg.n_tracks, cfg.n_neg, seen, cfg.seed)
    loader = DataLoader(ds, batch_size=cfg.batch_size, shuffle=True, num_workers=0)

    torch.manual_seed(cfg.seed)
    model = TwoTowerCF(cfg.n_playlists, cfg.n_tracks, cfg.embed_dim).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    history: list[float] = []
    for epoch in range(cfg.epochs):
        model.train()
        running = 0.0
        n_batches = 0
        for p, pos, neg in loader:
            p = p.to(device); pos = pos.to(device); neg = neg.to(device)
            loss = model(p, pos, neg)
            opt.zero_grad()
            loss.backward()
            opt.step()
            running += float(loss.item())
            n_batches += 1
        history.append(running / max(1, n_batches))
        print(f"epoch {epoch + 1}/{cfg.epochs}  bpr_loss={history[-1]:.4f}")

    return TrainedNCF(
        model=model.cpu(),
        config=cfg,
        playlist_index=playlist_index,
        track_index=track_index,
        history=history,
    )


def recommend(
    trained: TrainedNCF,
    playlist_ids: list[str],
    seen_per_playlist: dict[str, set[str]] | None = None,
    k: int = 50,
    batch_size: int = 256,
) -> list[list[str]]:
    """top-K track ids per playlist. masks already-seen tracks if provided.

    batched matmul keeps BLAS happy; per-playlist score arrays are not held.
    """
    reverse_tracks = trained.reverse_track_index()
    model = trained.model.eval()
    item_w = model.track_emb.weight.detach().cpu().numpy()
    user_w = model.playlist_emb.weight.detach().cpu().numpy()
    item_t = item_w.T

    out: list[list[str]] = [[] for _ in playlist_ids]
    valid: list[tuple[int, int]] = []
    for out_i, pid in enumerate(playlist_ids):
        idx = trained.playlist_index.get(pid)
        if idx is not None:
            valid.append((out_i, idx))

    for start in range(0, len(valid), batch_size):
        chunk = valid[start : start + batch_size]
        user_idx = np.array([i for _, i in chunk], dtype=np.int32)
        users = user_w[user_idx]                       # (B, D)
        scores = users @ item_t                         # (B, n_items)
        if seen_per_playlist:
            for row, (out_i, _) in enumerate(chunk):
                pid = playlist_ids[out_i]
                seen = seen_per_playlist.get(pid)
                if not seen:
                    continue
                seen_idx = [trained.track_index[t] for t in seen if t in trained.track_index]
                if seen_idx:
                    scores[row, seen_idx] = -np.inf
        top_k = np.argpartition(-scores, k, axis=1)[:, :k]
        for row, (out_i, _) in enumerate(chunk):
            cols = top_k[row]
            order = np.argsort(-scores[row, cols])
            out[out_i] = [reverse_tracks[j] for j in cols[order]]
    return out


def save(trained: TrainedNCF, path: str | Path) -> None:
    """write a single .pt with weights and indices. small enough for S3."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": trained.model.state_dict(),
            "config": trained.config.__dict__,
            "playlist_index": trained.playlist_index,
            "track_index": trained.track_index,
            "history": trained.history,
        },
        path,
    )


def load(path: str | Path) -> TrainedNCF:
    blob = torch.load(path, map_location="cpu", weights_only=False)
    cfg = TwoTowerConfig(**blob["config"])
    model = TwoTowerCF(cfg.n_playlists, cfg.n_tracks, cfg.embed_dim)
    model.load_state_dict(blob["state_dict"])
    return TrainedNCF(
        model=model,
        config=cfg,
        playlist_index=blob["playlist_index"],
        track_index=blob["track_index"],
        history=blob.get("history", []),
    )
