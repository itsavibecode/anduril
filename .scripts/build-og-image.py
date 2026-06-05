"""
Build the Anduril IPO Tracker Open Graph image.

Output: T:/ClaudeCodeRepo/anduril/og-image.png  (1200x630, the size every share
target expects)

Also outputs apple-touch-icon.png at 180x180 for iOS home-screen previews.

Run from T:\\ClaudeCodeRepo\\anduril with:
    python .scripts/build-og-image.py
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_OG = REPO / "og-image.png"
OUT_APPLE = REPO / "apple-touch-icon.png"

# Palette — matches the live site (var(--bg) etc.)
BG       = (10, 12, 17)         # #0a0c11
PANEL    = (18, 22, 31)         # #12161f
LINE     = (50, 58, 75)         # #323a4b
INK      = (238, 241, 246)      # #eef1f6
INK_DIM  = (166, 175, 192)      # #a6afc0
INK_FAINT= (121, 131, 154)      # #79839a
ACCENT   = (91, 157, 255)       # #5b9dff
ACCENT2  = (86, 214, 198)       # #56d6c6

FONTS = "C:/Windows/Fonts"
def f(name, size):
    return ImageFont.truetype(f"{FONTS}/{name}", size)

def text_size(draw, text, font):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t

# -----------------------------------------------------------------------------
# Open Graph image — 1200 x 630
# -----------------------------------------------------------------------------
W, H = 1200, 630
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img, "RGBA")

# Inset frame
PAD = 48
d.rounded_rectangle([PAD, PAD, W - PAD, H - PAD], radius=24,
                    outline=LINE, width=2)

# --- Brand row (top-left) ---------------------------------------------------
brand_x, brand_y = PAD + 36, PAD + 36
d.ellipse([brand_x, brand_y + 10, brand_x + 12, brand_y + 22], fill=ACCENT)
brand_font = f("Inter-SemiBold.ttf", 22)
d.text((brand_x + 22, brand_y + 4), "Anduril IPO", font=brand_font, fill=INK)
slash_w, _ = text_size(d, "Anduril IPO", brand_font)
d.text((brand_x + 22 + slash_w + 10, brand_y + 4), "/  Tracker",
       font=brand_font, fill=INK_FAINT)

# Status pill (top-right)
status_text = "PRE-IPO · NO S-1 FILED"
status_font = f("Inter-SemiBold.ttf", 14)
sw, sh = text_size(d, status_text, status_font)
sp_x2 = W - PAD - 36
sp_y = PAD + 36
d.rounded_rectangle([sp_x2 - sw - 28, sp_y, sp_x2, sp_y + sh + 14],
                    radius=999, outline=LINE, width=1)
d.ellipse([sp_x2 - sw - 22, sp_y + sh/2 + 1, sp_x2 - sw - 14, sp_y + sh/2 + 9],
          fill=ACCENT2)
d.text((sp_x2 - sw - 4, sp_y + 6), status_text, font=status_font, fill=ACCENT2)

# --- Big hero window --------------------------------------------------------
date_font = f("ariblk.ttf", 140)  # Arial Black — heaviest sans on Windows
date_text = "2026–27"
dw, _ = text_size(d, date_text, date_font)
ascent, descent = date_font.getmetrics()
date_visual_height = ascent + descent
date_y = 178
d.text(((W - dw) / 2, date_y), date_text, font=date_font, fill=INK)

sub_font = f("Inter-Medium.ttf", 24)
sub_text = "Estimated listing window  ·  valuation $61B  ·  not yet filed"
sw2, _ = text_size(d, sub_text, sub_font)
d.text(((W - sw2) / 2, date_y + date_visual_height + 8),
       sub_text, font=sub_font, fill=INK_DIM)

# --- Bottom row: ticker pill + valuation ------------------------------------
row_y = H - PAD - 36 - 110

# Ticker pill (left)
tk_x = PAD + 36
tk_w, tk_h = 300, 110
d.rounded_rectangle([tk_x, row_y, tk_x + tk_w, row_y + tk_h],
                    radius=14, fill=PANEL, outline=LINE, width=1)

lbl_font = f("Inter-SemiBold.ttf", 13)
d.text((tk_x + 22, row_y + 18), "TICKER", font=lbl_font, fill=INK_DIM)

ticker_font = f("consolab.ttf", 44)
d.text((tk_x + 22, row_y + 40), "TBD", font=ticker_font, fill=ACCENT)

exch_font = f("consolab.ttf", 13)
exch_text = "NYSE / NASDAQ?"
ew, eh = text_size(d, exch_text, exch_font)
d.rounded_rectangle([tk_x + tk_w - 22 - ew - 12, row_y + 18,
                     tk_x + tk_w - 22, row_y + 18 + eh + 6],
                    radius=4, fill=(86, 214, 198, 30))
d.text((tk_x + tk_w - 22 - ew - 6, row_y + 19), exch_text,
       font=exch_font, fill=ACCENT2)

# Valuation (right)
pr_w = 520
pr_x = W - PAD - 36 - pr_w
d.rounded_rectangle([pr_x, row_y, pr_x + pr_w, row_y + tk_h],
                    radius=14, fill=PANEL, outline=LINE, width=1)
d.text((pr_x + 26, row_y + 18), "LATEST PRIVATE VALUATION",
       font=lbl_font, fill=INK_DIM)
price_font = f("ariblk.ttf", 56)
d.text((pr_x + 26, row_y + 38), "$61B",
       font=price_font, fill=ACCENT2)
# small "Series H" tag on the right of the valuation card
sh_font = f("Inter-Medium.ttf", 16)
sht = "Series H · May 2026"
shw, shh = text_size(d, sht, sh_font)
d.text((pr_x + pr_w - 26 - shw, row_y + tk_h - 18 - shh), sht,
       font=sh_font, fill=INK_FAINT)

# --- Footer URL -------------------------------------------------------------
url_font = f("Inter-Medium.ttf", 18)
url_text = "anduril.bookhockeys.com"
uw, uh = text_size(d, url_text, url_font)
d.text(((W - uw) / 2, H - PAD - 18 - uh),
       url_text, font=url_font, fill=INK_FAINT)

img.save(OUT_OG, "PNG", optimize=True)
print(f"Wrote {OUT_OG}  ({OUT_OG.stat().st_size // 1024} KB)")

# -----------------------------------------------------------------------------
# Apple touch icon — 180 x 180 (angular peak / "A" mark on dark)
# -----------------------------------------------------------------------------
S = 180
icon = Image.new("RGB", (S, S), BG)
di = ImageDraw.Draw(icon)
di.rounded_rectangle([0, 0, S - 1, S - 1], radius=34, fill=BG)
# Outer A-frame / peak (matches the inline SVG favicon, scaled 64 -> 180)
outer = [
    (90, 31),     # apex
    (140.6, 143.4),  # bottom-right
    (115.3, 143.4),  # inner right base
    (90, 87.2),      # inner notch
    (64.7, 143.4),   # inner left base
    (39.4, 143.4),   # bottom-left
]
di.polygon(outer, fill=ACCENT)
# Inner accent triangle (the small teal core)
inner = [(90, 87.2), (104, 118.1), (76, 118.1)]
di.polygon(inner, fill=ACCENT2)

icon.save(OUT_APPLE, "PNG", optimize=True)
print(f"Wrote {OUT_APPLE}  ({OUT_APPLE.stat().st_size // 1024} KB)")
