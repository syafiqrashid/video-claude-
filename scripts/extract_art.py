"""Cut the illustrations out of the storyboard and prep them for the video.

Sketches are divided by the local paper colour so the paper becomes white, then
the page multiplies them onto its own paper background (no visible boxes).
Photos are cropped to their inner area; the page draws the white photo border.
Coordinates are in the 2x panel space (panel crop at (x0, 12), scaled 2x).
"""
import numpy as np
from PIL import Image, ImageFilter

SRC = "../assets/storyboard.png"
OUT = "assets/art/"
SCALE = 1080 / 458                       # storyboard panel -> 1080px wide video
PANELS = [12, 480, 948, 1417]
im = Image.open(SRC).convert("RGB")
PAPER = (236, 213, 164)   # matches --paper in index.html

def crop(panel, box):
    x0 = PANELS[panel]
    l, t, r, b = box
    c = im.crop((x0 + l / 2, 12 + t / 2, x0 + r / 2, 12 + b / 2))
    w, h = c.size
    c = c.resize((round(w * SCALE * 1.15), round(h * SCALE * 1.15)), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))

def sketch(name, panel, box, erase=(), feather=0.10):
    c = crop(panel, box)
    a = np.asarray(c).astype(np.float32)
    # local paper colour: heavy blur of the brightest content
    paper = np.asarray(c.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(40))).astype(np.float32)
    n = np.clip(a / np.maximum(paper, 1) * 255 * 1.04, 0, 255)
    h, w = n.shape[:2]
    # feathered alpha towards white at the edges so it melts into the paper
    yy, xx = np.mgrid[0:h, 0:w]
    f = np.minimum.reduce([xx / (w * feather), (w - xx) / (w * feather),
                           yy / (h * feather), (h - yy) / (h * feather), np.ones_like(xx, float)])
    f = np.clip(f, 0, 1) ** 1.5
    sx, sy = w / ((box[2] - box[0])), h / ((box[3] - box[1]))
    for (l, t, r, b) in erase:            # wipe text that overlapped the art
        L, T, R, B = [round(v) for v in ((l - box[0]) * sx, (t - box[1]) * sy, (r - box[0]) * sx, (b - box[1]) * sy)]
        f[max(T, 0):B, max(L, 0):R] = 0
    f = np.asarray(Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(25))) / 255.0
    n = 255 - (255 - n) * f[..., None]
    # turn "multiply onto paper" into a plain RGBA image (blend modes are unreliable
    # inside filtered/transformed layers): alpha from the darkest channel, colour
    # chosen so that compositing over PAPER equals PAPER * n.
    P = np.array(PAPER, np.float32)
    nn = n / 255.0
    a = np.clip(1 - nn.min(axis=2), 0, 1)
    C = P * (nn - 1 + a[..., None]) / np.maximum(a[..., None], 1e-3)
    rgba = np.dstack([np.clip(C, 0, 255), a * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT + name + ".png", optimize=True)

def photo(name, panel, box):
    c = crop(panel, box)
    c.save(OUT + name + ".jpg", quality=92)

import os; os.makedirs(OUT, exist_ok=True)
sketch("f1-street", 0, (0, 632, 916, 1312), erase=[(0, 632, 670, 652), (0, 632, 575, 905)], feather=0.06)
photo("f2-crowd", 1, (84, 612, 754, 843))
photo("f2-flag", 1, (169, 868, 816, 1096))
photo("f2-street", 1, (119, 1120, 595, 1298))
sketch("f3-skyline", 2, (0, 1040, 916, 1312), feather=0.08)
sketch("f4-soldiers", 3, (20, 430, 900, 748), feather=0.08)
sketch("f4-people", 3, (40, 948, 880, 1296), feather=0.07)
print("done")
