"""matplotlib draw of the Camelot wheel with optional track markers."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

# ordered around the wheel (1 -> 12), with inner ring = A (minor), outer = B (major).
RING_ORDER = list(range(1, 13))


def draw(track_codes: list[str] | None = None, highlight: str | None = None, title: str = "Camelot wheel"):
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={"projection": "polar"})
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    angles = np.linspace(0, 2 * math.pi, 12, endpoint=False)

    # outer ring (major / B)
    for i, n in enumerate(RING_ORDER):
        ax.fill_between([angles[i] - math.pi/12, angles[i] + math.pi/12], 1.05, 1.55,
                        color="#f0e5d6", edgecolor="#d6c6ad")
        ax.text(angles[i], 1.30, f"{n}B", ha="center", va="center",
                fontsize=9, fontfamily="monospace", color="#1f1c1a")

    # inner ring (minor / A)
    for i, n in enumerate(RING_ORDER):
        ax.fill_between([angles[i] - math.pi/12, angles[i] + math.pi/12], 0.55, 1.05,
                        color="#fbf3e7", edgecolor="#e0d2b8")
        ax.text(angles[i], 0.80, f"{n}A", ha="center", va="center",
                fontsize=8, fontfamily="monospace", color="#5b524a")

    if track_codes:
        for code in track_codes:
            pt = _code_to_point(code)
            if pt is None:
                continue
            angle, r = pt
            ax.plot(angle, r, marker="o", markersize=7, color="#8b3a3a",
                    markeredgecolor="white", markeredgewidth=1.2, zorder=5)

    if highlight:
        pt = _code_to_point(highlight)
        if pt is not None:
            angle, r = pt
            ax.plot(angle, r, marker="*", markersize=18, color="#b8924a",
                    markeredgecolor="white", markeredgewidth=1.2, zorder=6)

    ax.set_ylim(0, 1.7)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title(title, fontfamily="sans-serif", fontsize=12, pad=10, color="#1f1c1a")
    fig.patch.set_facecolor("#f5efe6")
    return fig


def _code_to_point(code: str) -> tuple[float, float] | None:
    if not code or len(code) < 2:
        return None
    try:
        n = int(code[:-1])
    except ValueError:
        return None
    letter = code[-1]
    if n < 1 or n > 12 or letter not in "AB":
        return None
    angle = (n - 1) * (2 * math.pi / 12)
    r = 1.30 if letter == "B" else 0.80
    return angle, r
