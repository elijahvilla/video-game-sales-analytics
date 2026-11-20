"""Static charts for the README (Tableau Public dashboard is the interactive version)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
OUT = ROOT / "docs"
INK, MUTED, ACCENT, ACCENT2 = "#1f2937", "#9ca3af", "#2563eb", "#dc2626"


def _style(ax, title):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK)


def market_trend():
    df = pd.read_csv(RES / "market_yoy_growth.csv")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(df.year, df.sales_m, color=MUTED, label="Units sold (millions)")
    ax.plot(df.year, df.moving_avg_3y, color=ACCENT, lw=2.5, label="3-year moving average")
    peak = df.loc[df.sales_m.idxmax()]
    ax.annotate(f"Peak {int(peak.year)}: {peak.sales_m:.0f}M", (peak.year, peak.sales_m),
                xytext=(peak.year + 2.2, peak.sales_m * 1.02), color=INK, arrowprops=dict(arrowstyle="-", color=MUTED))
    _style(ax, "Tracked unit sales peak in 2008")
    ax.set_ylim(0, peak.sales_m * 1.15)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "market_trend.png", dpi=150)


def jp_vs_na():
    df = pd.read_csv(RES / "jp_vs_na_genre_preference.csv").sort_values("jp_index")
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = [ACCENT2 if v >= 1 else ACCENT for v in df.jp_index]
    ax.barh(df.genre, df.jp_index, color=colors)
    ax.axvline(1, color=INK, lw=1)
    for y, v in enumerate(df.jp_index):
        ax.text(v + 0.05, y, f"{v:.2f}×", va="center", color=INK, fontsize=9)
    _style(ax, "Japan over-indexes on RPGs (3.6×) and skips shooters (0.22×)")
    ax.set_xlabel("Genre share in Japan ÷ genre share in North America")
    fig.tight_layout()
    fig.savefig(OUT / "jp_vs_na_genres.png", dpi=150)


def platform_life():
    df = pd.read_csv(RES / "platform_peak_year.csv").head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(df.platform, df.lifetime_m, color=ACCENT)
    for y, (v, peak) in enumerate(zip(df.lifetime_m, df.peak_year)):
        ax.text(v + 10, y, f"{v:.0f}M · peak {peak}", va="center", color=INK, fontsize=9)
    _style(ax, "Lifetime units by platform, with peak year")
    ax.set_xlim(0, df.lifetime_m.max() * 1.3)
    fig.tight_layout()
    fig.savefig(OUT / "platform_lifetime.png", dpi=150)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    market_trend(); jp_vs_na(); platform_life()
    print("charts written to", OUT)
