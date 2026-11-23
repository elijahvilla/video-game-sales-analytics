"""Draw the dashboard's pixel-art header (original art, retro-game style).

Usage: python tableau/make_header.py <path-to-PressStart2P-Regular.ttf>
Font: Press Start 2P (SIL Open Font License), from Google Fonts.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "assets" / "header.png"
W, H = 2400, 400   # drawn at 2x, shown at 1200 x 200
PX = 8             # one "pixel" of pixel art

BG = (22, 19, 15)
GOLD = (212, 175, 55)
GOLD_DIM = (120, 98, 40)
CREAM = (232, 223, 200)
MUTED = (154, 143, 120)
RED, BLUE, YELLOW, GREEN = (229, 37, 33), (46, 111, 219), (255, 203, 5), (63, 163, 77)


def block(d, x, y, color, n=1):
    d.rectangle([x, y, x + PX * n - 1, y + PX * n - 1], fill=color)


def glow(img, cx, cy, r, color):
    """Soft radial glow behind the tree."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for i in range(r, 0, -6):
        a = int(70 * (1 - i / r) ** 2)
        ld.ellipse([cx - i, cy - i, cx + i, cy + i], fill=color + (a,))
    img.alpha_composite(layer)


def golden_tree(d, ox, oy):
    """Blocky golden tree: trunk plus layered canopy."""
    for y in range(0, 14):  # trunk
        w = 2 if y < 10 else 3 + (y - 10)
        for x in range(-w // 2, w // 2 + 1):
            block(d, ox + x * PX, oy + (20 + y) * PX, GOLD if x % 2 else GOLD_DIM)
    rng = random.Random(7)
    for gy in range(0, 21):          # round canopy: filled ellipse of blocks
        for gx in range(-14, 15):
            if (gx / 14) ** 2 + ((gy - 10) / 10.5) ** 2 <= 1:
                edge = (gx / 14) ** 2 + ((gy - 10) / 10.5) ** 2 > 0.72
                if edge and rng.random() < 0.35:
                    continue
                lit = gx + gy < 4 and rng.random() < 0.55      # light from the upper left
                shade = gx + gy > 18 and rng.random() < 0.6
                c = (250, 225, 120) if lit else GOLD_DIM if shade else (GOLD if rng.random() < 0.85 else GOLD_DIM)
                block(d, ox + gx * PX, oy + gy * PX, c)


def ring(d, cx, cy, r=22):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=8)
    d.arc([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], 200, 260, fill=(255, 240, 170), width=4)


def coin(d, cx, cy):
    d.rectangle([cx - 12, cy - 20, cx + 12, cy + 20], fill=YELLOW)
    d.rectangle([cx - 4, cy - 12, cx + 4, cy + 12], fill=(200, 150, 0))


def main(font_path):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    rng = random.Random(42)
    keep_clear = [(380, 50, 1560, 390), (1810, 40, 2240, 380), (40, 20, 330, 380)]
    for _ in range(220):  # starfield, kept off the text and art
        x, y = rng.randrange(0, W // PX) * PX, rng.randrange(0, H // PX) * PX
        if any(a <= x <= c and b <= y <= e for a, b, c, e in keep_clear):
            continue
        block(d, x, y, rng.choice([MUTED, GOLD_DIM, (60, 54, 44)]))

    glow(img, 180, 200, 210, (212, 175, 55))
    d = ImageDraw.Draw(img)
    golden_tree(d, 180, 40)

    small = ImageFont.truetype(font_path, 22)
    big = ImageFont.truetype(font_path, 52)
    mid = ImageFont.truetype(font_path, 22)
    d.text((400, 70), "PRESS START  >  1980-2016", font=small, fill=GOLD)
    d.text((400, 130), "36 YEARS OF", font=big, fill=CREAM)
    d.text((400, 205), "VIDEO GAME SALES", font=big, fill=GOLD)
    d.text((400, 300), "16,187 GAMES  *  31 PLATFORMS  *  8.79 BILLION UNITS", font=mid, fill=MUTED)

    # region color key as 4 pixel "lives"
    for i, c in enumerate([RED, BLUE, YELLOW, GREEN]):
        block(d, 400 + i * 40, 350, c, 3)

    # HUD, top right
    d.text((1830, 60), "HI-SCORE", font=small, fill=RED)
    d.text((1830, 100), "678.2M", font=ImageFont.truetype(font_path, 40), fill=CREAM)
    d.text((1830, 160), "UNITS IN 2008", font=small, fill=MUTED)
    for i in range(5):
        ring(d, 1860 + i * 64, 260)
    for i in range(4):
        coin(d, 1876 + i * 72, 340)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main(sys.argv[1])
