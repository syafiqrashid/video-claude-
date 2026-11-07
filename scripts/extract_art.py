"""Cut the illustrations out of the storyboard and prep them for the video.

Sketches are divided by the local paper colour so the paper becomes white, then
the page multiplies them onto its own paper background (no visible boxes).
Photos are cropped to their inner area; the page draws the white photo border.
Coordinates are in the 2x panel space (panel crop at (x0, 12), scaled 2x).
"""
import numpy as np
from PIL import Image, ImageFilter

# v1 storyboard: photo cards; v2 storyboard (revised): sketches
BOARDS = {
    "v1": ("../assets/storyboard.png", [12, 480, 948, 1417], 12),
    "v2": ("../assets/storyboard-v2.png", [10, 479, 948, 1418], 10),
}
OUT = "assets/art/"
SCALE = 1080 / 458                       # storyboard panel -> 1080px wide video
IMS = {k: Image.open(v[0]).convert("RGB") for k, v in BOARDS.items()}
PAPER = (236, 213, 164)   # matches --paper in index.html

def crop(panel, box, board="v2"):
    x0, y0 = BOARDS[board][1][panel], BOARDS[board][2]
    l, t, r, b = box
    c = IMS[board].crop((x0 + l / 2, y0 + t / 2, x0 + r / 2, y0 + b / 2))
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
    f = np.asarray(Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(25))) / 255.0
    sx, sy = w / ((box[2] - box[0])), h / ((box[3] - box[1]))
    e = np.ones_like(f)
    for (l, t, r, b) in erase:            # wipe text that overlapped the art
        L, T, R, B = [round(v) for v in ((l - box[0]) * sx, (t - box[1]) * sy, (r - box[0]) * sx, (b - box[1]) * sy)]
        e[max(T, 0):B, max(L, 0):R] = 0
    e = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))) / 255.0
    f = f * e
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
    c = crop(panel, box, "v1")
    c.save(OUT + name + ".jpg", quality=92)

import os; os.makedirs(OUT, exist_ok=True)
sketch("f1-street", 0, (0, 612, 916, 1292), erase=[(0, 612, 552, 792), (0, 612, 300, 868)], feather=0.04)
photo("f2-crowd", 1, (84, 612, 754, 843))
photo("f2-flag", 1, (169, 868, 816, 1096))
photo("f2-street", 1, (119, 1120, 595, 1298))
sketch("f3-skyline", 2, (0, 988, 916, 1268), feather=0.07)
sketch("f4-soldiers", 3, (30, 392, 900, 726), feather=0.08)
sketch("f4-people", 3, (40, 946, 880, 1274), feather=0.07)
print("done")
