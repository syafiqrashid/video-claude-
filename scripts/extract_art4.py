"""Video 4 (kesejahteraan): cut photos, sketch and logo out of the storyboard.

Run from the repo root. Boxes are native panel pixels (panels 466x827).
"""
import numpy as np
from PIL import Image, ImageFilter

im = Image.open("video4/raw/storyboard.png").convert("RGB")
PANELS = [(3, 2), (476, 2), (950, 2), (1425, 2)]
OUT = "video4/assets/art/"
UP = 1080 / 466 * 1.15

def crop(panel, box):
    x0, y0 = PANELS[panel]
    l, t, r, b = box
    c = im.crop((x0 + l, y0 + t, x0 + r, y0 + b))
    c = c.resize((round(c.width * UP), round(c.height * UP)), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

def photo(name, panel, box):
    crop(panel, box).save(OUT + name + ".jpg", quality=92)

def cutout(name, panel, box, feather=0.04, fade_top=0.0, fade_bottom=0.0):
    """Paper -> transparent so the art sits on the page paper."""
    c = crop(panel, box)
    a = np.asarray(c).astype(np.float32)
    paper = np.asarray(c.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(40))).astype(np.float32)
    nn = np.clip(a / np.maximum(paper, 1) * 1.03, 0, 1)
    h, w = nn.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    f = np.minimum.reduce([xx / (w * feather), (w - xx) / (w * feather), yy / (h * feather), (h - yy) / (h * feather), np.ones_like(xx, float)])
    if fade_top: f = np.minimum(f, yy / (h * fade_top))
    if fade_bottom: f = np.minimum(f, (h - yy) / (h * fade_bottom))
    f = np.clip(f, 0, 1)
    al = np.clip(1 - nn.min(axis=2), 0, 1) * f
    P = np.array([240, 217, 168], np.float32)          # page paper (--paper in index.html)
    keep = np.clip((a - P * (1 - al[..., None])) / np.maximum(al[..., None], 1e-3), 0, 255)
    rgba = np.dstack([keep, al * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT + name + ".png", optimize=True)

cutout("f1-city", 0, (0, 418, 466, 652), feather=0.03, fade_bottom=0.12)
photo("f2-palace", 1, (93, 295, 404, 398))
photo("f2-family", 1, (29, 417, 200, 579))
photo("f3-towers", 2, (54, 132, 374, 300))
photo("f3-terrace", 2, (50, 499, 416, 627))
cutout("f4-logo", 3, (64, 118, 426, 256), feather=0.02)
photo("f4-crowd", 3, (44, 456, 418, 622))
print("done")
