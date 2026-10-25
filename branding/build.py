"""Generate Kupas Daily logo SVGs (text outlined to paths) and PNG exports.

Usage: python3 branding/build.py
Requires: fonttools, Inter font family, Node + Playwright (for PNG export, see export.js).
"""
import subprocess
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = Path(__file__).parent
FONT_DIR = Path("/usr/share/fonts/opentype/inter")

NAVY = "#0B1F3A"
AMBER = "#F5A524"
SLATE = "#5B6B84"
PAPER = "#FFFFFF"


class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.cap = self.tt["OS/2"].sCapHeight

    def width(self, text, cap_px, tracking=0.0):
        s = cap_px / self.cap
        adv = sum(self.gs[self.cmap[ord(c)]].width for c in text) * s
        return adv + tracking * (len(text) - 1)

    def path(self, text, x, baseline, cap_px, tracking=0.0):
        s = cap_px / self.cap
        pen = SVGPathPen(self.gs)
        for c in text:
            g = self.gs[self.cmap[ord(c)]]
            g.draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
            x += g.width * s + tracking
        return pen.getCommands()


DISPLAY = Font(FONT_DIR / "InterDisplay-ExtraBold.otf")
TEXT = Font(FONT_DIR / "Inter-SemiBold.otf")


def icon(x, y, size, tile, mark, flap):
    """Rounded tile with a peeled top-right corner and a geometric K."""
    k = size / 120
    t = lambda px, py: f"{x + px * k:.2f},{y + py * k:.2f}"
    return f"""
  <path fill="{tile}" d="M{t(26,0)} L{t(82,0)} L{t(120,38)} L{t(120,94)} Q{t(120,120)} {t(94,120)} L{t(26,120)} Q{t(0,120)} {t(0,94)} L{t(0,26)} Q{t(0,0)} {t(26,0)} Z"/>
  <path fill="{flap}" d="M{t(82,0)} L{t(120,38)} L{t(90,38)} Q{t(82,38)} {t(82,30)} Z"/>
  <path fill="{mark}" d="M{t(30,30)} L{t(46,30)} L{t(46,90)} L{t(30,90)} Z M{t(45,68)} L{t(69,44)} L{t(91,44)} L{t(45,90)} Z M{t(55.5,75.5)} L{t(66.5,64.5)} L{t(92,90)} L{t(70,90)} Z"/>"""


def wordmark(x, cap_top, cap, word_fill, sub_fill, align="left"):
    """KUPAS over tracked DAILY, both the same width."""
    kupas_w = DISPLAY.width("KUPAS", cap, tracking=cap * 0.02)
    sub_cap = cap * 0.30
    raw = TEXT.width("DAILY", sub_cap)
    tracking = (kupas_w - raw) / 4
    if align == "center":
        x -= kupas_w / 2
    base1 = cap_top + cap
    base2 = base1 + cap * 0.30 + sub_cap
    return (
        f'\n  <path fill="{word_fill}" d="{DISPLAY.path("KUPAS", x, base1, cap, cap * 0.02)}"/>'
        f'\n  <path fill="{sub_fill}" d="{TEXT.path("DAILY", x, base2, sub_cap, tracking)}"/>',
        kupas_w,
        base2 - cap_top,
    )


def svg(w, h, body, bg=None):
    rect = f'\n  <rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="Kupas Daily">'
        f"<title>Kupas Daily</title>{rect}{body}\n</svg>\n"
    )


def horizontal(tile, mark, flap, word, sub, bg=None):
    pad, size, gap, cap = 40, 120, 30, 62
    words, ww, wh = wordmark(pad + size + gap, 0, cap, word, sub)
    top = pad + (size - wh) / 2
    words, _, _ = wordmark(pad + size + gap, top, cap, word, sub)
    return svg(pad * 2 + size + gap + ww, pad * 2 + size, icon(pad, pad, size, tile, mark, flap) + words, bg)


def stacked(tile, mark, flap, word, sub, bg=None):
    pad, size, cap = 48, 140, 70
    _, ww, wh = wordmark(0, 0, cap, word, sub)
    w = max(size, ww) + pad * 2
    words, _, _ = wordmark(w / 2, pad + size + 40, cap, word, sub, align="center")
    h = pad + size + 40 + wh + pad
    return svg(w, h, icon((w - size) / 2, pad, size, tile, mark, flap) + words, bg)


def app_icon(tile, mark, flap, bg):
    # Full-bleed square (for avatars / app icons, platforms apply their own mask).
    body = f'\n  <rect width="512" height="512" fill="{bg}"/>' + icon(76, 76, 360, tile, mark, flap)
    return svg(512, 512, body)


FILES = {
    "kupas-daily-horizontal.svg": horizontal(NAVY, PAPER, AMBER, NAVY, SLATE),
    "kupas-daily-horizontal-dark.svg": horizontal(PAPER, NAVY, AMBER, PAPER, AMBER, bg=NAVY),
    "kupas-daily-stacked.svg": stacked(NAVY, PAPER, AMBER, NAVY, SLATE),
    "kupas-daily-stacked-dark.svg": stacked(PAPER, NAVY, AMBER, PAPER, AMBER, bg=NAVY),
    "kupas-daily-icon.svg": icon(0, 0, 120, NAVY, PAPER, AMBER).join(
        ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" role="img" aria-label="Kupas Daily"><title>Kupas Daily</title>', "\n</svg>\n"]
    ),
    "kupas-daily-avatar.svg": app_icon(PAPER, NAVY, AMBER, NAVY),
}


def export_png(names):
    subprocess.run(["node", str(OUT / "export.js"), *names], check=True)


if __name__ == "__main__":
    for name, content in FILES.items():
        (OUT / name).write_text(content)
    export_png(FILES)
    print("wrote", ", ".join(FILES))
