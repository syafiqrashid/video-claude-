"""Video 2 (manfaat merdeka): cut photos and sketches out of the storyboard.

Run from the repo root. Coordinates are in 2x panel space: panel crop at
(x0, 13), scaled 2x (992 x 1762). Photos are cropped above their name labels;
the page draws the frame and label.
"""
import numpy as np
from PIL import Image, ImageFilter

im = Image.open("video2/raw/storyboard.png").convert("RGB")
PANELS = [13, 522, 1031, 1539]
OUT = "video2/assets/art/"
UP = 1080 / 992 * 1.2                      # 2x-panel px -> video px, with headroom

def crop(panel, box, up=UP):
    x0 = PANELS[panel]
    l, t, r, b = box
    c = im.crop((x0 + l / 2, 13 + t / 2, x0 + r / 2, 13 + b / 2))
    c = c.resize((round(c.width * 2 * up), round(c.height * 2 * up)), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

def photo(name, panel, box):
    crop(panel, box).save(OUT + name + ".jpg", quality=92)

def cutout(name, panel, box, paper, erase=(), feather=0.05):
    """Page paper -> transparent (keeps darker torn-paper pieces), RGBA PNG."""
    c = crop(panel, box)
    a = np.asarray(c).astype(np.float32)
    P = np.array(paper, np.float32)
    nn = np.clip(a / P, 0, 1)
    h, w = nn.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    f = np.minimum.reduce([xx / (w * feather), (w - xx) / (w * feather), yy / (h * feather),
                           (h - yy) / (h * feather), np.ones_like(xx, float)])
    f = np.clip(f, 0, 1)
    sx, sy = w / (box[2] - box[0]), h / (box[3] - box[1])
    e = np.ones_like(f)
    for (l, t, r, b) in erase:
        L, T, R, B = [round(v) for v in ((l - box[0]) * sx, (t - box[1]) * sy, (r - box[0]) * sx, (b - box[1]) * sy)]
        e[max(T, 0):B, max(L, 0):R] = 0
    e = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))) / 255.0
    f = f * e
    al = np.clip((1 - nn.min(axis=2)) * 1.6, 0, 1) * f      # boost so torn paper stays opaque-ish
    C = P * (nn - 1 + al[..., None]) / np.maximum(al[..., None], 1e-3)
    rgba = np.dstack([np.clip(C, 0, 255), al * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT + name + ".png", optimize=True)

PAPER = tuple(int(v) for v in np.median(np.asarray(im.crop((PANELS[0] + 300, 13 + 150, PANELS[0] + 470, 13 + 330))).reshape(-1, 3), axis=0))
print("paper", PAPER)
# frame 1: KL skyline + LRT on torn paper, hibiscus scrap
cutout("f1-city", 0, (170, 640, 992, 1462), PAPER,
       erase=[(170, 640, 842, 890), (170, 880, 252, 948), (600, 640, 720, 745), (170, 1336, 778, 1462)], feather=0.02)
# frame 2
photo("f2-school", 1, (54, 514, 686, 876))
photo("f2-health", 1, (252, 986, 934, 1320))
# frame 3
photo("f3-school", 2, (54, 414, 460, 776))
photo("f3-health", 2, (520, 418, 932, 778))
photo("f3-train", 2, (50, 908, 470, 1290))
photo("f3-work", 2, (530, 912, 943, 1296))
# frame 4 flag
PAPER4 = tuple(int(v) for v in np.median(np.asarray(im.crop((PANELS[3] + 60, 13 + 520, PANELS[3] + 160, 13 + 600))).reshape(-1, 3), axis=0))
cutout("f4-flag", 3, (360, 1028, 660, 1228), PAPER4, feather=0.04)
print("done")
