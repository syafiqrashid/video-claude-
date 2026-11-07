"""Video 3 (patriotisme): cut photos out of the 2x2 storyboard.

Run from the repo root. Coordinates are native panel pixels (panels are 566x1006;
panel origins below). The page draws photo frames, labels, X mark and icons.
"""
from PIL import Image, ImageFilter

im = Image.open("video3/raw/storyboard.png").convert("RGB")
PANELS = [(12, 12), (590, 12), (12, 1030), (590, 1030)]
OUT = "video3/assets/art/"
UP = 1080 / 566 * 1.15

def photo(name, panel, box):
    x0, y0 = PANELS[panel]
    l, t, r, b = box
    c = im.crop((x0 + l, y0 + t, x0 + r, y0 + b))
    c = c.resize((round(c.width * UP), round(c.height * UP)), Image.LANCZOS)
    c.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2)).save(OUT + name + ".jpg", quality=92)

photo("f2-flaghand", 1, (50, 238, 338, 536))
photo("f4-p1", 3, (54, 322, 266, 449))
photo("f4-p2", 3, (292, 318, 504, 444))
photo("f4-p3", 3, (54, 468, 268, 591))
photo("f4-p4", 3, (292, 454, 505, 591))
photo("f4-p5", 3, (76, 607, 259, 733))
photo("f4-p6", 3, (278, 609, 474, 732))
print("done")
