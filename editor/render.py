# Motion-graphics renderer: storyboard layers + animations + karaoke subtitles.
import cv2, numpy as np, pickle, json, sys, os, math, subprocess, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WORK = "/tmp/claude-0/-home-user-video-claude-/2a734288-29af-5c47-8d50-5a13f3989741/scratchpad/work/"
FONTS = "/tmp/claude-0/-home-user-video-claude-/2a734288-29af-5c47-8d50-5a13f3989741/scratchpad/fonts/"
F_BLACK = FONTS + "f2.ttf"      # Montserrat Black
F_XBOLD = FONTS + "f1.ttf"      # Montserrat ExtraBold
for f in os.listdir(FONTS):
    if f.endswith(".ttf"):
        nm = subprocess.run(["fc-scan", "--format", "%{fullname}", FONTS + f], capture_output=True, text=True).stdout
        if "Montserrat Black" in nm: F_BLACK = FONTS + f
        elif "Montserrat ExtraBold" in nm: F_XBOLD = FONTS + f

OUT_W = int(os.environ.get("OUT_W", 540))
OUT_H = OUT_W * 16 // 9
FPS = int(os.environ.get("FPS", 30))
PW, PH = 453, 810
S = OUT_W / PW
YOFF = -int(round(3 * S))
SUB_Y0, SUB_Y1 = int(600 * S) + YOFF, OUT_H - int(12 * S)

TL = json.load(open(WORK + "timeline.json"))
WORDS, PANS, VODUR = TL["words"], TL["panels"], TL["dur"]
END_HOLD = 1.8
TOTAL = VODUR + END_HOLD
LEAD = 0.18  # visuals start slightly before the voice for each panel

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def e_out_cubic(u): return 1 - (1 - u) ** 3
def e_in_cubic(u): return u ** 3
def e_inout(u): return 3 * u * u - 2 * u ** 3
def e_out_back(u, s=1.70158):
    u -= 1
    return u * u * ((s + 1) * u + s) + 1
def e_out_elastic(u):
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 2 ** (-9 * u) * math.sin((u * 7 - 0.75) * (2 * math.pi) / 3) + 1
def e_bounce(u):
    n1, d1 = 7.5625, 2.75
    if u < 1 / d1: return n1 * u * u
    if u < 2 / d1: u -= 1.5 / d1; return n1 * u * u + 0.75
    if u < 2.5 / d1: u -= 2.25 / d1; return n1 * u * u + 0.9375
    u -= 2.625 / d1; return n1 * u * u + 0.984375

# ---------------------------------------------------------------- timing helpers
def panel_bounds():
    b = []
    for i, p in enumerate(PANS):
        st = max(0.0, p["t"] - LEAD) if i else 0.0
        en = (PANS[i + 1]["t"] - LEAD) if i + 1 < len(PANS) else TOTAL
        b.append((p["k"], st, en, p["t"]))
    return b
BOUNDS = panel_bounds()

def norm(w): return re.sub(r"[^\w%.\-]", "", w.lower())

def resolve_t(spec, k, pstart, pvo, pend):
    if isinstance(spec, (int, float)):
        return pstart + spec
    m = re.match(r"w:([^+\-]+(?:-[a-zA-Z]+)?[.,]?)([+\-][\d.]+)?$", spec)
    word = m.group(1); off = float(m.group(2) or 0)
    target = norm(word)
    cands = [w for w in WORDS if pvo - 0.4 <= w["s"] < pend + 0.3]
    for w in cands:
        nw = norm(w["w"])
        if nw == target or nw.rstrip(".,") == target.rstrip(".,"):
            return max(pstart, w["s"] + off)
    for w in cands:
        if norm(w["w"]).startswith(target.rstrip(".,")):
            return max(pstart, w["s"] + off)
    print("WARN word not found", k, spec, file=sys.stderr)
    return pstart + 0.5

# ---------------------------------------------------------------- assets
def to_rgba_scaled(rgb_bgr, a):
    rgba = np.dstack([rgb_bgr[..., ::-1], (a * 255).astype(np.uint8)])
    im = Image.fromarray(rgba.astype(np.uint8), "RGBA")
    w, h = im.size
    im = im.resize((max(1, round(w * S)), max(1, round(h * S))), Image.LANCZOS)
    if S > 1.5:  # upscaled storyboard art: gentle unsharp mask on colour only
        a = im.split()[3]
        im = im.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2)).convert("RGBA")
        im.putalpha(a)
    return im

class Layer:
    pass

def text_mask_inpaint(rgb, box, light):
    """remove the digits inside box from layer-local rgb, return clean rgb + text colour"""
    x0, y0, x1, y1 = box
    sub = rgb[y0:y1, x0:x1].astype(np.float32)
    lum = sub.mean(2)
    med = np.median(lum)
    if light:
        m = lum > med + 0.35 * (lum.max() - med)
    else:
        m = lum < med - 0.35 * (med - lum.min())
    m = m.astype(np.uint8)
    col = np.median(sub[m > 0], axis=0) if m.sum() > 10 else (np.array([255, 255, 255]) if light else np.array([30, 30, 30]))
    if light:  # stronger: use brightest pixels for colour
        sel = sub[lum > np.percentile(lum, 92)]
        col = np.median(sel, axis=0)
    else:
        sel = sub[lum < np.percentile(lum, 8)]
        col = np.median(sel, axis=0)
    mm = np.zeros(rgb.shape[:2], np.uint8)
    mm[y0:y1, x0:x1] = cv2.dilate(m, np.ones((5, 5), np.uint8)) * 255
    clean = cv2.inpaint(rgb, mm, 4, cv2.INPAINT_TELEA)
    return clean, col  # BGR colour

_font_cache = {}
def font(path, size):
    k = (path, size)
    if k not in _font_cache: _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]

def render_count_text(txt, box_w, box_h, color_bgr, italic):
    """render txt in heavy font to fit box (panel px) -> RGBA at output scale"""
    sc = S * 2
    W, H = int(box_w * sc), int(box_h * sc)
    size = int(H * 1.30)
    f = font(F_BLACK, size)
    while True:
        bb = f.getbbox(txt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        if (tw <= W * 1.02 and th <= H * 1.0) or size < 8: break
        size = int(size * 0.94); f = font(F_BLACK, size)
    im = Image.new("RGBA", (W + 40, H + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = tuple(int(c) for c in color_bgr[::-1]) + (255,)
    d.text(((W + 40 - tw) / 2 - bb[0], (H + 40 - th) / 2 - bb[1]), txt, font=f, fill=col)
    if italic:
        im = im.transform(im.size, Image.AFFINE, (1, 0.2, -0.2 * im.size[1] / 2, 0, 1, 0), Image.BICUBIC)
    im = im.resize(((W + 40) // 2, (H + 40) // 2), Image.LANCZOS)
    return im

def build_layers(prep, key, pstart, pvo, pend):
    out = []
    for L in prep[key]["layers"]:
        d = L["d"]
        o = Layer()
        o.name, o.anim, o.rect = d["name"], d["anim"], d["rect"]
        o.t0 = resolve_t(d["t"], key, pstart, pvo, pend)
        o.dur = d.get("d", 0.5)
        o.kb = d.get("kb", 0)
        o.glow = d.get("glow", False)
        o.sfx = d.get("sfx")
        o.img = to_rgba_scaled(L["rgb"], L["a"])
        x0, y0, x1, y1 = o.rect
        o.x, o.y = x0 * S, y0 * S + YOFF
        o.glow_img = None
        if o.glow:
            g = o.img.copy()
            alpha = g.split()[3]
            g = g.filter(ImageFilter.GaussianBlur(6 * S))
            o.glow_img = g
        o.count = None
        c = d.get("count")
        if c:
            bx0, by0, bx1, by1 = c["box"]
            lb = (bx0 - x0, by0 - y0, bx1 - x0, by1 - y0)
            clean, col = text_mask_inpaint(L["rgb"], lb, c["light"])
            o.clean_img = to_rgba_scaled(clean, L["a"])
            o.count = dict(c, lb=lb, col=col, t0=None, cache={})
        out.append(o)
    return out

def count_frame(o, t):
    c = o.count
    ct0 = o.t0 + o.dur * 0.35
    u = (t - ct0) / c["dur"]
    if u >= 1: return o.img, None
    u = clamp(u)
    v = c["frm"] + (c["to"] - c["frm"]) * e_out_cubic(u)
    if isinstance(c["to"], int) and isinstance(c["frm"], int):
        v = int(round(v))
    txt = c["fmt"].format(v)
    if txt not in c["cache"]:
        lb = c["lb"]
        timg = render_count_text(txt, lb[2] - lb[0], lb[3] - lb[1], c["col"], c.get("italic", False))
        base = o.clean_img.copy()
        cx = (lb[0] + lb[2]) / 2 * S; cy = (lb[1] + lb[3]) / 2 * S
        base.alpha_composite(timg, (int(cx - timg.size[0] / 2), int(cy - timg.size[1] / 2)))
        c["cache"][txt] = base
    return c["cache"][txt], txt

# ---------------------------------------------------------------- per-layer state
def layer_state(o, t, pend, exit_mode):
    """returns dict(dx,dy,s,a,wipe,(dir)) or None if invisible"""
    u = (t - o.t0) / o.dur
    if u < 0: return None
    u = clamp(u)
    st = dict(dx=0.0, dy=0.0, s=1.0, a=1.0, wipe=None, rot=0.0)
    A = o.anim
    if A == "fade": st["a"] = e_inout(u)
    elif A == "fade_d":
        st["a"] = e_out_cubic(u); st["dy"] = -18 * S * (1 - e_out_cubic(u))
    elif A in ("slide_l", "slide_r"):
        e = e_out_back(u, 1.1)
        dist = 230 * S
        st["dx"] = (-dist if A == "slide_l" else dist) * (1 - e)
        st["a"] = clamp(u * 3)
    elif A == "slide_u":
        e = e_out_back(u, 0.9); st["dy"] = 260 * S * (1 - e); st["a"] = clamp(u * 3)
    elif A == "pop":
        e = e_out_back(u, 2.2); st["s"] = 0.15 + 0.85 * e; st["a"] = clamp(u * 4)
    elif A == "zoom":
        e = e_out_elastic(u); st["s"] = 1.9 - 0.9 * e; st["a"] = clamp(u * 4)
    elif A == "scale_up":
        e = e_out_cubic(u); st["s"] = 0.82 + 0.18 * e; st["a"] = e_inout(u)
    elif A.startswith("wipe"):
        st["wipe"] = (A[-1], e_inout(u))
    elif A == "stamp":
        e = e_in_cubic(u); st["s"] = 2.4 - 1.4 * e; st["a"] = clamp(u * 2.5); st["rot"] = 0
    elif A == "drop":
        st["dy"] = -170 * S * (1 - e_bounce(u)); st["a"] = clamp(u * 4)
    # idle motion
    since = t - (o.t0 + o.dur)
    if since > 0:
        if o.kb:
            span = max(1.0, pend - (o.t0 + o.dur))
            st["s"] *= 1 + (o.kb - 1) * clamp(since / span)
        if A in ("zoom", "pop") and o.count is not None or A == "zoom":
            st["s"] *= 1 + 0.012 * math.sin(since * 3.2)
    # exit
    if exit_mode is not None:
        kind, eu = exit_mode
        if kind == "soft":
            st["a"] *= 1 - e_inout(eu); st["dy"] -= 26 * S * e_in_cubic(eu); st["s"] *= 1 - 0.04 * eu
        elif kind == "push":
            st["dx"] -= OUT_W * 1.05 * e_in_cubic(eu); st["a"] *= 1 - 0.3 * eu
        elif kind == "final":
            st["a"] *= 1 - e_inout(eu)
    return st

def apply_layer(canvas, o, img, st, t):
    w, h = img.size
    s = st["s"]
    if st["wipe"] is not None:
        dirc, f = st["wipe"]
        if f <= 0: return
        img = img.copy()
        m = Image.new("L", img.size, 0)
        dm = ImageDraw.Draw(m)
        if dirc == "l": dm.rectangle([0, 0, int(w * f), h], fill=255)
        elif dirc == "r": dm.rectangle([int(w * (1 - f)), 0, w, h], fill=255)
        elif dirc == "d": dm.rectangle([0, 0, w, int(h * f)], fill=255)
        elif dirc == "u": dm.rectangle([0, int(h * (1 - f)), w, h], fill=255)
        a = img.split()[3]
        from PIL import ImageChops
        img.putalpha(ImageChops.multiply(a, m))
    if abs(s - 1) > 1e-3:
        nw, nh = max(1, int(w * s)), max(1, int(h * s))
        img2 = img.resize((nw, nh), Image.BILINEAR)
        px = o.x + w / 2 - nw / 2 + st["dx"]; py = o.y + h / 2 - nh / 2 + st["dy"]
    else:
        img2 = img; px = o.x + st["dx"]; py = o.y + st["dy"]
    if st["a"] < 0.999:
        if st["a"] <= 0.003: return
        a = img2.split()[3].point(lambda v, k=st["a"]: int(v * k))
        img2 = img2.copy(); img2.putalpha(a)
    paste(canvas, img2, int(round(px)), int(round(py)))
    if o.glow_img is not None:
        since = t - o.t0
        k = (0.35 + 0.3 * math.sin(since * 4.0)) * st["a"] * clamp(since / o.dur)
        if k > 0.02:
            g = o.glow_img
            if abs(s - 1) > 1e-3: g = g.resize(img2.size, Image.BILINEAR)
            garr = np.asarray(g).astype(np.float32)
            add_glow(canvas, garr, int(round(px)), int(round(py)), k)

def paste(canvas, img, x, y):
    W, H = canvas.size
    if x >= W or y >= H or x + img.size[0] <= 0 or y + img.size[1] <= 0: return
    canvas.alpha_composite(img, (max(0, x), max(0, y)),
                           (max(0, -x), max(0, -y), min(img.size[0], W - x), min(img.size[1], H - y)))

GLOW_BUF = {}
def add_glow(canvas, garr, x, y, k):
    GLOW_BUF.setdefault("list", []).append((garr, x, y, k))

def flush_glow(frame):
    for garr, x, y, k in GLOW_BUF.get("list", []):
        h, w = garr.shape[:2]
        X0, Y0 = max(0, x), max(0, y); X1, Y1 = min(OUT_W, x + w), min(OUT_H, y + h)
        if X1 <= X0 or Y1 <= Y0: continue
        g = garr[Y0 - y:Y1 - y, X0 - x:X1 - x]
        add = g[..., :3] * (g[..., 3:4] / 255.0) * k
        frame[Y0:Y1, X0:X1] = np.minimum(255, frame[Y0:Y1, X0:X1] + add * 0.9)
    GLOW_BUF["list"] = []

# ---------------------------------------------------------------- background
def make_bg(prep):
    paper = prep["s1p1"]["paper"].astype(np.float32)[..., ::-1]  # RGB
    c_center = np.median(paper[250:450, 150:300].reshape(-1, 3), 0)
    c_edge = np.median(np.concatenate([paper[20:80, 5:30].reshape(-1, 3), paper[20:80, -30:-5].reshape(-1, 3),
                                       paper[700:790, 5:30].reshape(-1, 3), paper[700:790, -30:-5].reshape(-1, 3)]), 0)
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:OUT_H, 0:OUT_W]
    r = np.sqrt(((xx - OUT_W / 2) / (OUT_W * 0.62)) ** 2 + ((yy - OUT_H * 0.47) / (OUT_H * 0.62)) ** 2)
    k = np.clip(r, 0, 1.25) ** 1.6
    bg = c_center[None, None] * (1 - k[..., None]) + c_edge[None, None] * k[..., None]
    bg = bg.astype(np.float32)
    # faint grid
    step = 12.5 * S
    gx = (np.abs(((xx + 0.5) % step) - step / 2) > step / 2 - 0.6 * max(1, S / 1.6))
    gy = (np.abs(((yy + 0.5) % step) - step / 2) > step / 2 - 0.6 * max(1, S / 1.6))
    grid = (gx | gy).astype(np.float32)
    bg -= grid[..., None] * np.array([14, 18, 22]) * 0.55
    # grunge (low-freq) + grain
    lf = cv2.GaussianBlur(rng.normal(0, 1, (OUT_H, OUT_W)).astype(np.float32), (0, 0), 60 * S)
    lf /= lf.std() + 1e-6
    bg *= (1 + 0.025 * lf)[..., None]
    fib = cv2.GaussianBlur(rng.normal(0, 1, (OUT_H, OUT_W)).astype(np.float32), (0, 0), sigmaX=6 * S, sigmaY=1.2 * S)
    fib /= fib.std() + 1e-6
    bg *= (1 + 0.018 * fib)[..., None]
    bg += rng.normal(0, 2.6, (OUT_H, OUT_W, 1))
    return np.clip(bg, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- subtitles
def build_captions():
    caps = []
    cur = []
    bound_times = [p["t"] for p in PANS]
    def flush():
        if cur: caps.append(list(cur)); cur.clear()
    for i, w in enumerate(WORDS):
        if cur:
            # break on panel boundary
            if any(cur[-1]["s"] < bt <= w["s"] + 0.01 for bt in bound_times): flush()
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
        if w["w"].endswith((".", "?", "!")) or (w["w"].endswith(",") and len(txt) > 14) or len(txt) > 30 or len(cur) >= 6:
            flush()
        elif nxt and nxt["s"] - w["e"] > 0.5:
            flush()
    flush()
    merged = []
    for c in caps:
        if merged and len(c) == 1 and not any(merged[-1][-1]["s"] < bt <= c[0]["s"] + 0.01 for bt in bound_times) \
                and len(" ".join(x["w"] for x in merged[-1] + c)) <= 50:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    caps = merged
    out = []
    for i, c in enumerate(caps):
        st = c[0]["s"] - 0.08
        en = caps[i + 1][0]["s"] - 0.08 if i + 1 < len(caps) else c[-1]["e"] + 0.8
        en = min(en, c[-1]["e"] + 0.9)
        out.append(dict(words=c, st=st, en=en))
    return out
CAPS = build_captions()

SUB_FONT = None
def sub_layout(cap):
    if "layout" in cap: return cap["layout"]
    fs = int(31 * S)
    f = font(F_BLACK, fs)
    maxw = OUT_W - int(44 * S)
    words = [w["w"] for w in cap["words"]]
    space = f.getlength(" ")
    lines = [[]]; widths = [0]
    for i, w in enumerate(words):
        ww = f.getlength(w)
        add = ww + (space if lines[-1] else 0)
        if widths[-1] + add > maxw and lines[-1]:
            lines.append([]); widths.append(0); add = ww
        lines[-1].append(i); widths[-1] += add
    lh = int(fs * 1.38)
    total_h = lh * len(lines)
    cy = (SUB_Y0 + SUB_Y1) / 2 - 4 * S
    y = cy - total_h / 2
    pos = []
    for li, ln in enumerate(lines):
        x = (OUT_W - widths[li]) / 2
        for i in ln:
            ww = f.getlength(words[i])
            pos.append((i, x, y + li * lh, ww))
            x += ww + space
    cap["layout"] = (f, fs, pos, lh)
    return cap["layout"]

def draw_subs(canvas, t):
    cap = None
    for c in CAPS:
        if c["st"] <= t < c["en"]: cap = c; break
    if cap is None: return
    f, fs, pos, lh = sub_layout(cap)
    u = clamp((t - cap["st"]) / 0.12)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    words = cap["words"]
    act = None
    for i, w in enumerate(words):
        if w["s"] - 0.03 <= t: act = i
    for i, x, y, ww in pos:
        w = words[i]
        if i == act:
            pad = 5 * S
            d.rounded_rectangle([x - pad, y - 1 * S, x + ww + pad, y + fs * 1.13], radius=int(5 * S), fill=(255, 205, 0, 255))
    for i, x, y, ww in pos:
        w = words[i]
        spoken = w["s"] - 0.03 <= t
        col = (190, 20, 30, 255) if i == act else ((22, 30, 70, 255) if spoken else (22, 30, 70, 150))
        d.text((x, y), w["w"], font=f, fill=col, stroke_width=0)
    if u < 1:
        a = layer.split()[3].point(lambda v: int(v * u))
        layer.putalpha(a)
        dy = int((1 - e_out_cubic(u)) * 10 * S)
        canvas.alpha_composite(layer, (0, dy) if dy else (0, 0)) if dy == 0 else paste(canvas, layer, 0, dy)
    else:
        canvas.alpha_composite(layer)

# ---------------------------------------------------------------- scene
class Scene:
    def __init__(self):
        prep = pickle.load(open(WORK + "layers.pkl", "rb"))
        self.bg = make_bg(prep)
        self.panels = []
        for i, (k, st, en, vo) in enumerate(BOUNDS):
            nxt = BOUNDS[i + 1][0] if i + 1 < len(BOUNDS) else None
            exit_kind = "final" if nxt is None else ("push" if nxt.endswith("p1") else "soft")
            exit_dur = {"final": 1.2, "push": 0.42, "soft": 0.28}[exit_kind]
            lay = build_layers(prep, k, st, vo, en)
            self.panels.append(dict(k=k, st=st, en=en, vo=vo, layers=lay, exit=exit_kind, exit_dur=exit_dur))
        self.shake = []  # (t, amp)
        for p in self.panels:
            for o in p["layers"]:
                if o.anim == "stamp": self.shake.append((o.t0 + o.dur, 5 * S))
                if o.anim == "zoom": self.shake.append((o.t0 + o.dur * 0.25, 2.5 * S))

    def frame(self, t):
        canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
        for p in self.panels:
            # visible window: entry from st, exit ends at en + overlap
            if p["exit"] == "final":
                ex0 = TOTAL - p["exit_dur"]; ex1 = TOTAL
            elif p["exit"] == "push":
                ex0 = p["en"] - 0.12; ex1 = ex0 + p["exit_dur"]
            else:
                ex0 = p["en"] - 0.1; ex1 = ex0 + p["exit_dur"]
            if t < p["st"] - 0.01 or t > ex1: continue
            exit_mode = None
            if t >= ex0: exit_mode = (p["exit"], clamp((t - ex0) / (ex1 - ex0)))
            for o in p["layers"]:
                if t < o.t0: continue
                st = layer_state(o, t, p["en"], exit_mode)
                if st is None: continue
                img = o.img
                if o.count is not None:
                    img, _ = count_frame(o, t)
                apply_layer(canvas, o, img, st, t)
        draw_subs(canvas, t)
        frame = self.bg.astype(np.float32).copy()
        arr = np.asarray(canvas).astype(np.float32)
        a = arr[..., 3:4] / 255.0
        frame = frame * (1 - a) + arr[..., :3] * a
        flush_glow(frame)
        # camera shake
        sh = 0
        for ts, amp in self.shake:
            if 0 <= t - ts < 0.25:
                sh = amp * (1 - (t - ts) / 0.25) * math.sin((t - ts) * 90)
        out = np.clip(frame, 0, 255).astype(np.uint8)
        if abs(sh) > 0.5:
            M = np.float32([[1, 0, sh * 0.6], [0, 1, sh]])
            out = cv2.warpAffine(out, M, (OUT_W, OUT_H), borderMode=cv2.BORDER_REFLECT)
        # global fade in/out
        if t < 0.35 and not os.environ.get("NOFADE"): out = (out * (t / 0.35)).astype(np.uint8)
        if t > TOTAL - 0.6 and not os.environ.get("NOFADE"): out = (out * clamp((TOTAL - t) / 0.6)).astype(np.uint8)
        return out

def sfx_events(scene):
    """collect (time, type, gain) for the audio mixer"""
    ev = []
    for i, p in enumerate(scene.panels):
        for o in p["layers"]:
            s = o.sfx
            if s == "none": continue
            if s is None:
                s = {"slide_l": "swoosh", "slide_r": "swoosh", "slide_u": "whoosh", "pop": "pop", "zoom": "impact",
                     "scale_up": "soft", "wipe_l": "swish", "wipe_d": "swish", "wipe_u": "swish", "wipe_r": "swish",
                     "stamp": "stamp", "drop": "coin", "fade": None, "fade_d": None}.get(o.anim)
            if s: ev.append((o.t0, s, 1.0, o.name))
            if o.count is not None:
                c = o.count
                ct0 = o.t0 + o.dur * 0.35
                ev.append((ct0, "ticks:%.2f" % c["dur"], 1.0, o.name))
                ev.append((ct0 + c["dur"], "ding", 0.8, o.name))
        if p["exit"] == "push":
            ev.append((p["en"] - 0.12, "transition", 1.0, "push"))
    ev.sort()
    # thin out: same type within 0.12s
    out = []
    for e in ev:
        if out and e[1] == out[-1][1] and e[0] - out[-1][0] < 0.12: continue
        out.append(e)
    return out

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "stills":
        sc = Scene()
        ts = [float(x) for x in sys.argv[2:]]
        for t in ts:
            Image.fromarray(sc.frame(t)).save(WORK + f"still_{t:07.2f}.png")
    elif mode == "sfx":
        sc = Scene()
        json.dump(sfx_events(sc), open(WORK + "sfx_events.json", "w"), indent=0)
        print(len(sfx_events(sc)), "events")
    elif mode == "chunk":
        f0, f1, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        sc = Scene()
        crf = os.environ.get("CRF", "24")
        preset = os.environ.get("PRESET", "veryfast")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                              "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p", outp], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(sc.frame(fi / FPS).tobytes())
            if (fi - f0) % 300 == 0: print(outp, fi, flush=True)
        p.stdin.close(); p.wait()
