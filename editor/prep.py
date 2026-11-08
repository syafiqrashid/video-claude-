# Extract animatable RGBA layers from storyboard panels.
import cv2, numpy as np, pickle, sys, os
from layers import PANELS

WORK = "/tmp/claude-0/-home-user-video-claude-/2a734288-29af-5c47-8d50-5a13f3989741/scratchpad/work/"
PW, PH = 453, 810


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def fill_holes(m):
    """m: uint8 0/1. fill enclosed holes."""
    h, w = m.shape
    ff = m.copy() * 255
    pad = np.zeros((h + 2, w + 2), np.uint8)
    pad[1:-1, 1:-1] = ff
    mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(pad, mask, (0, 0), 128)
    holes = (pad[1:-1, 1:-1] == 0)
    return np.maximum(m, holes.astype(np.uint8))


def lab(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)


def extract_panel(key):
    img = cv2.imread(WORK + f"panels/{key}.png")  # BGR 453x810
    defs = PANELS[key]
    n = len(defs)
    # union mask of all rects + black box region -> paper estimate
    um = np.zeros((PH, PW), np.uint8)
    for d in defs:
        x0, y0, x1, y1 = d["rect"]
        um[y0:y1, x0:x1] = 255
    um[584:, :] = 255
    small = cv2.resize(img, (PW // 3, PH // 3), interpolation=cv2.INTER_AREA)
    sm = cv2.resize(um, (PW // 3, PH // 3), interpolation=cv2.INTER_NEAREST)
    paper = cv2.inpaint(small, sm, 9, cv2.INPAINT_TELEA)
    paper = cv2.GaussianBlur(paper, (0, 0), 6)
    paper = cv2.resize(paper, (PW, PH), interpolation=cv2.INTER_CUBIC)

    layers = []
    claimed = []  # per layer full-size claim mask (float)
    for i, d in enumerate(defs):
        x0, y0, x1, y1 = d["rect"]
        crop = img[y0:y1, x0:x1].copy()
        # background estimate behind element: inpaint rect from its surroundings in the panel
        pad = 6
        X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(PW, x1 + pad), min(PH, y1 + pad)
        region = img[Y0:Y1, X0:X1].copy()
        rm = np.zeros(region.shape[:2], np.uint8)
        rm[y0 - Y0 + 1:y1 - Y0 - 1, x0 - X0 + 1:x1 - X0 - 1] = 255
        # is the element sitting on paper or inside another element?
        ring = region[rm == 0]
        ring_paper = paper[Y0:Y1, X0:X1][rm == 0]
        on_paper = np.median(np.linalg.norm(lab(ring[None])[0] - lab(ring_paper[None])[0], axis=1)) < 14
        if on_paper:
            under = paper[y0:y1, x0:x1]
            e0, e1 = 9, 24
        else:
            sc = 2
            rs = cv2.resize(region, (region.shape[1] // sc, region.shape[0] // sc), interpolation=cv2.INTER_AREA)
            ms = cv2.resize(rm, (rs.shape[1], rs.shape[0]), interpolation=cv2.INTER_NEAREST)
            under = cv2.inpaint(rs, ms, 7, cv2.INPAINT_TELEA)
            under = cv2.GaussianBlur(under, (0, 0), 2)
            under = cv2.resize(under, (region.shape[1], region.shape[0]), interpolation=cv2.INTER_CUBIC)
            under = under[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
            e0, e1 = 14, 34
        dist = np.linalg.norm(lab(crop) - lab(under), axis=2)
        a = smoothstep(e0, e1, dist)
        a = cv2.GaussianBlur(a, (0, 0), 0.8)
        binm = (a > 0.45).astype(np.uint8)
        binm = cv2.morphologyEx(binm, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        # remove tiny specks
        nl, lbl, st, _ = cv2.connectedComponentsWithStats(binm)
        keep = np.zeros_like(binm)
        for j in range(1, nl):
            if st[j, 4] >= max(30, 0.002 * binm.size):
                keep[lbl == j] = 1
        filled = fill_holes(keep)
        core = cv2.erode(filled, np.ones((3, 3), np.uint8))
        a = np.maximum(a * (cv2.dilate(keep, np.ones((7, 7), np.uint8)) > 0), core.astype(np.float32))
        a = np.clip(a, 0, 1)
        # fade out the very edge of rect to avoid hard lines
        fe = 3
        ramp = np.ones_like(a)
        for k in range(fe):
            v = (k + 1) / (fe + 1)
            ramp[k, :] = np.minimum(ramp[k, :], v); ramp[-k - 1, :] = np.minimum(ramp[-k - 1, :], v)
            ramp[:, k] = np.minimum(ramp[:, k], v); ramp[:, -k - 1] = np.minimum(ramp[:, -k - 1], v)
        a = a * ramp
        full = np.zeros((PH, PW), np.float32)
        full[y0:y1, x0:x1] = a
        layers.append(dict(d=d, rgb=crop, a=a))
        claimed.append(full)

    # ownership: later layers claim pixels -> earlier layers inpaint those areas
    for i in range(n):
        x0, y0, x1, y1 = defs[i]["rect"]
        cm = np.zeros((y1 - y0, x1 - x0), np.float32)
        for j in range(i + 1, n):
            cm = np.maximum(cm, claimed[j][y0:y1, x0:x1])
        if cm.max() < 0.3:
            continue
        m = (cm > 0.25).astype(np.uint8)
        m = cv2.dilate(m, np.ones((5, 5), np.uint8))
        L = layers[i]
        L["rgb"] = cv2.inpaint(L["rgb"], m * 255, 5, cv2.INPAINT_TELEA)
        a8 = (L["a"] * 255).astype(np.uint8)
        a8 = cv2.inpaint(a8, m * 255, 5, cv2.INPAINT_TELEA)
        L["a"] = a8.astype(np.float32) / 255
    return layers, paper


def make_background():
    """single global paper background (panel res, BGR float)"""
    _, paper = extract_panel("s1p1")
    bg = cv2.GaussianBlur(paper, (0, 0), 10).astype(np.float32)
    return bg


if __name__ == "__main__":
    out = {}
    keys = sys.argv[1:] or list(PANELS.keys())
    for k in keys:
        layers, paper = extract_panel(k)
        out[k] = dict(layers=layers, paper=paper)
        print("prepped", k, len(layers), flush=True)
    pickle.dump(out, open(WORK + "layers.pkl", "wb"))
