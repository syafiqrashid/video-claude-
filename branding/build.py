"""Generate Kupas Daily logo SVGs (text outlined to paths) and PNG exports.

Usage: python3 branding/build.py
Requires: fonttools, Inter font family, Node + Playwright (for PNG export, see export.js).
"""
import subprocess
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
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

    def bounds(self, char, x, baseline, cap_px):
        s = cap_px / self.cap
        pen = BoundsPen(self.gs)
        self.gs[self.cmap[ord(char)]].draw(pen)
        x0, y0, x1, y1 = pen.bounds
        return x + x0 * s, baseline - y1 * s, x + x1 * s, baseline - y0 * s


DISPLAY = Font(FONT_DIR / "InterDisplay-ExtraBold.otf")
TEXT = Font(FONT_DIR / "Inter-SemiBold.otf")
MIN_BOLD = Font(FONT_DIR / "InterDisplay-SemiBold.otf")
MIN_LIGHT = Font(FONT_DIR / "InterDisplay-Light.otf")


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


def peel(x0, y0, x1, y1, fill):
    """The folded-corner triangle: right angle at bottom-left."""
    return f'\n  <path fill="{fill}" d="M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f} L{x0:.2f},{y1:.2f} Z"/>'


def minimal(word, sub, accent, bg=None):
    """Lowercase 'kupas daily'; the dot of the i is replaced by the peel triangle."""
    pad, cap = 36, 60
    gap = cap * 0.26
    base = pad + cap * 1.05
    kupas_w = MIN_BOLD.width("kupas", cap)
    x2 = pad + kupas_w + gap
    daily = "da\u0131ly"  # dotless i
    body = (
        f'\n  <path fill="{word}" d="{MIN_BOLD.path("kupas", pad, base, cap)}"/>'
        f'\n  <path fill="{sub}" d="{MIN_LIGHT.path(daily, x2, base, cap)}"/>'
    )
    # Locate the i: its stem is the dotless glyph; its dot sits where the regular i's top is.
    ix = x2 + MIN_LIGHT.width("da", cap)
    sx0, stem_top, sx1, _ = MIN_LIGHT.bounds("\u0131", ix, base, cap)
    _, dot_top, _, _ = MIN_LIGHT.bounds("i", ix, base, cap)
    size = cap * 0.2
    bottom = stem_top - (stem_top - dot_top) * 0.28
    body += peel(sx0, bottom - size, sx0 + size, bottom, accent)
    w = x2 + MIN_LIGHT.width(daily, cap) + pad
    return svg(w, base + cap * 0.32 + pad, body, bg)


def minimal_mark(mark, accent, size=120, pad=0, bg=None):
    """The geometric k on its own, with the peel triangle in the top-right."""
    k = (size - pad * 2) / 120
    t = lambda px, py: f"{pad + px * k:.2f},{pad + py * k:.2f}"
    body = (
        f'\n  <path fill="{mark}" d="M{t(14,6)} L{t(34,6)} L{t(34,114)} L{t(14,114)} Z '
        f'M{t(33,82)} L{t(69,46)} L{t(96,46)} L{t(33,109)} Z '
        f'M{t(48,94)} L{t(62,80)} L{t(96,114)} L{t(68,114)} Z"/>'
        f'\n  <path fill="{accent}" d="M{t(76,6)} L{t(106,36)} L{t(76,36)} Z"/>'
    )
    return svg(size, size, body, bg)


FILES = {
    "kupas-daily-horizontal.svg": horizontal(NAVY, PAPER, AMBER, NAVY, SLATE),
    "kupas-daily-horizontal-dark.svg": horizontal(PAPER, NAVY, AMBER, PAPER, AMBER, bg=NAVY),
    "kupas-daily-stacked.svg": stacked(NAVY, PAPER, AMBER, NAVY, SLATE),
    "kupas-daily-stacked-dark.svg": stacked(PAPER, NAVY, AMBER, PAPER, AMBER, bg=NAVY),
    "kupas-daily-icon.svg": icon(0, 0, 120, NAVY, PAPER, AMBER).join(
        ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" role="img" aria-label="Kupas Daily"><title>Kupas Daily</title>', "\n</svg>\n"]
    ),
    "kupas-daily-avatar.svg": app_icon(PAPER, NAVY, AMBER, NAVY),
    "kupas-daily-minimal.svg": minimal(NAVY, NAVY, AMBER),
    "kupas-daily-minimal-dark.svg": minimal(PAPER, PAPER, AMBER, bg=NAVY),
    "kupas-daily-minimal-mark.svg": minimal_mark(NAVY, AMBER),
    "kupas-daily-minimal-avatar.svg": minimal_mark(NAVY, AMBER, size=512, pad=136, bg=PAPER),
}


def export_png(names):
    subprocess.run(["node", str(OUT / "export.js"), *names], check=True)


if __name__ == "__main__":
    for name, content in FILES.items():
        (OUT / name).write_text(content)
    export_png(FILES)
    print("wrote", ", ".join(FILES))
