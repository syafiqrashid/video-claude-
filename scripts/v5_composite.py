"""Video 5 step 3: put the speaker (and the real wooden table) in the studio.

Mask = person alpha (RVM) OR everything below the table edge. The table edge
is found per frame from the wood colour and smoothed over time, so the real
desk stays and the room behind is replaced by video5/studio/studio.png.
The speaker is lightly graded (contrast, colour, sharpening) and edge-wrapped
with studio light so the cut-out sits in the scene. Writes video5/work/comp.mp4
(silent; the cleaned voice is added later).
"""
import subprocess, numpy as np, cv2

W, H = 1080, 1920
bg = cv2.cvtColor(cv2.imread("video5/studio/studio.png"), cv2.COLOR_BGR2RGB).astype(np.float32)
bg_blur = cv2.GaussianBlur(bg, (0, 0), 25)

def frames(path, fmt, ch):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", fmt, "-"], stdout=subprocess.PIPE)
    n = W * H * ch
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            return
        yield np.frombuffer(b, np.uint8).reshape(H, W, ch) if ch > 1 else np.frombuffer(b, np.uint8).reshape(H, W)

# pass 1: table top and front edge per frame
edges, bottoms = [], []
for f in frames("video5/work/edit.mov", "rgb24", 3):
    small = cv2.resize(f, (270, 480))
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    wood = ((hsv[..., 0] >= 6) & (hsv[..., 0] <= 22) & (hsv[..., 1] > 90) & (hsv[..., 2] > 45)).astype(np.float32)
    # ignore the centre where the speaker's arms are; use the left and right thirds
    frac = np.r_[wood[:, :70].mean(1)] * 0.5 + wood[:, -70:].mean(1) * 0.5
    y0 = 180
    run = 0; edge = 470
    for y in range(y0, 470):
        run = run + 1 if frac[y] > 0.6 else 0
        if run >= 8:
            edge = y - 7; break
    # front edge of the table: first run of non-wood rows below the top edge
    bot = 480
    run = 0
    for y in range(edge + 20, 480):
        run = run + 1 if frac[y] < 0.25 else 0
        if run >= 6:
            bot = y - 5; break
    edges.append(edge * 4)
    bottoms.append(bot * 4)
edges = np.array(edges, float)
# median smooth (camera shake is slow); never let it jump within a shot
k = 9
pad = np.pad(edges, k, mode="edge")
edges_s = np.array([np.median(pad[i:i + 2 * k + 1]) for i in range(len(edges))])
pad = np.pad(np.array(bottoms, float), k, mode="edge")
bottoms_s = np.array([np.median(pad[i:i + 2 * k + 1]) for i in range(len(bottoms))])
np.save("video5/work/table_edge.npy", np.stack([edges_s, bottoms_s]))
print("table front range", bottoms_s.min(), bottoms_s.max())
print("table edge range", edges_s.min(), edges_s.max())

yy = np.arange(H, dtype=np.float32)[:, None]
KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30",
                        "-i", "-", "-c:v", "libx264", "-crf", "15", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "video5/work/comp.mp4"], stdin=subprocess.PIPE)
for i, (f, a) in enumerate(zip(frames("video5/work/edit.mov", "rgb24", 3), frames("video5/work/alpha.mkv", "gray", 1))):
    fg = f.astype(np.float32)
    # grade: gentle S-curve, a touch more colour, slightly cooler shadows to match the studio
    x = fg / 255
    x = x + 0.10 * (x - 0.5) * (1 - np.abs(2 * x - 1))           # contrast
    lum = x.mean(2, keepdims=True)
    x = lum + (x - lum) * 1.08                                    # saturation
    x = x * np.array([1.0, 0.99, 1.02], np.float32)               # white balance toward the studio
    fg = np.clip(x, 0, 1) * 255
    fg = cv2.addWeighted(fg, 1.35, cv2.GaussianBlur(fg, (0, 0), 1.6), -0.35, 0)   # sharpen
    e = edges_s[i] + 6
    table = np.clip((yy - e) / 10, 0, 1) * np.clip((bottoms_s[i] - 4 - yy) / 6, 0, 1)
    # fast-moving hands come out semi-transparent (motion blur); firm them up:
    # levels on the matte, then a small close so blurred fingers stay solid
    al = np.clip((a.astype(np.float32) / 255 - 0.06) / 0.5, 0, 1)
    al = cv2.morphologyEx(al, cv2.MORPH_CLOSE, KERNEL)
    m = np.maximum(al, np.broadcast_to(table, (H, W)))
    m = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
    # light wrap: studio light bleeding over the speaker's edges
    edge = np.clip(m * (1 - m) * 4, 0, 1)
    fg = fg * (1 - 0.35 * edge) + bg_blur * 0.35 * edge
    out = fg * m + bg * (1 - m)
    enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    if i % 300 == 0:
        print(i, flush=True)
enc.stdin.close(); enc.wait()
print("done")
