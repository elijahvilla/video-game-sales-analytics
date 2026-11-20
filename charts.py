"""Charts for the README.

Color scheme is inspired by Elden Ring (my favorite game): Erdtree gold on a dark
background, parchment text, and scarlet-rot red for the contrast color.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
OUT = ROOT / "docs"

BG = "#14120e"         # near-black, warm
TEXT = "#e9e2cf"       # parchment
MUTED = "#8c857a"      # ash
GOLD = "#c9a14a"       # Erdtree gold
GOLD_LIGHT = "#ecd08a"
ROT = "#a3412c"        # scarlet rot
GRACE = LinearSegmentedColormap.from_list("grace", [BG, "#4a3b1c", GOLD, GOLD_LIGHT])

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": TEXT, "axes.labelcolor": TEXT, "xtick.color": MUTED, "ytick.color": TEXT,
    "axes.edgecolor": MUTED, "font.family": "serif",
    "font.serif": ["Garamond", "Palatino Linotype", "Georgia", "DejaVu Serif"], "font.size": 12,
})


def _title(ax, title, sub=None):
    ax.set_title(title, loc="left", fontsize=18, color=GOLD_LIGHT, pad=22 if sub else 10)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=11, color=MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def market_trend():
    df = pd.read_csv(RES / "market_yoy_growth.csv")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(df.year, df.sales_m, color="#3a3222", edgecolor=GOLD, linewidth=0.6, label="Units sold (millions)")
    ax.plot(df.year, df.moving_avg_3y, color=GOLD_LIGHT, lw=2.5, label="3-year moving average")
    peak = df.loc[df.sales_m.idxmax()]
    ax.annotate(f"2008 peak: {peak.sales_m:.0f}M units", (peak.year, peak.sales_m),
                xytext=(peak.year + 2.2, peak.sales_m * 1.02), color=TEXT,
                arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.set_ylim(0, peak.sales_m * 1.15)
    _title(ax, "The rise and fall of boxed game sales", "Units tracked by VGChartz per release year, 1995 to 2016")
    ax.legend(frameon=False, loc="upper left", labelcolor=TEXT)
    fig.tight_layout()
    fig.savefig(OUT / "market_trend.png", dpi=150)


def jp_vs_na():
    df = pd.read_csv(RES / "jp_vs_na_genre_preference.csv").sort_values("jp_index")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = [GOLD if v >= 1 else ROT for v in df.jp_index]
    ax.barh(df.genre, df.jp_index, color=colors)
    ax.axvline(1, color=MUTED, lw=1, ls="--")
    for y, v in enumerate(df.jp_index):
        ax.text(v + 0.05, y, f"{v:.2f}x", va="center", color=TEXT, fontsize=11)
    _title(ax, "Japan plays different games", "Genre share in Japan divided by genre share in North America (1.0 = same)")
    ax.set_xlim(0, df.jp_index.max() * 1.15)
    fig.tight_layout()
    fig.savefig(OUT / "jp_vs_na_genres.png", dpi=150)


def platform_life():
    df = pd.read_csv(RES / "platform_peak_year.csv").head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh(df.platform, df.lifetime_m, color=GOLD)
    for y, (v, peak) in enumerate(zip(df.lifetime_m, df.peak_year)):
        ax.text(v + 12, y, f"{v:.0f}M  (peak {peak})", va="center", color=TEXT, fontsize=11)
    _title(ax, "Lifetime units by platform", "Top 12 platforms in the dataset, with each one's best year")
    ax.set_xlim(0, df.lifetime_m.max() * 1.32)
    fig.tight_layout()
    fig.savefig(OUT / "platform_lifetime.png", dpi=150)


def genre_heatmap():
    df = pd.read_csv(RES / "genre_share_by_decade.csv")
    grid = df.pivot(index="genre", columns="decade", values="share_pct").fillna(0)
    grid = grid.loc[grid.sum(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(8, 5.6))
    ax.imshow(grid.values, cmap=GRACE, aspect="auto")
    ax.set_xticks(range(len(grid.columns)), grid.columns)
    ax.set_yticks(range(len(grid.index)), grid.index)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            v = grid.values[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=10,
                    color=BG if v > 18 else TEXT)
    _title(ax, "What each decade played", "Share of that decade's units by genre")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(OUT / "genre_by_decade.png", dpi=150)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    market_trend(); jp_vs_na(); platform_life(); genre_heatmap()
    print("charts written to", OUT)
