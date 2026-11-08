# Synthesize SFX track from events, then mix VO + BGM + SFX.
import numpy as np, soundfile as sf, json, subprocess, sys
from scipy.signal import butter, lfilter, sosfilt

WORK = "/tmp/claude-0/-home-user-video-claude-/2a734288-29af-5c47-8d50-5a13f3989741/scratchpad/work/"
SR = 48000
rng = np.random.default_rng(7)

def env_ar(n, a, r):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / r)
    return e

def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)

def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)

def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)

def sweep_noise(dur, f0, f1, f2, peak=0.45):
    """noise through a band-pass whose centre sweeps f0->f1->f2; amplitude swells to peak position"""
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    blk = 256
    t = np.arange(0, n, blk) / n
    zi = None
    for bi, i in enumerate(range(0, n, blk)):
        u = t[bi]
        fc = f0 + (f1 - f0) * (u / peak) if u < peak else f1 + (f2 - f1) * ((u - peak) / (1 - peak))
        sos = butter(2, [max(60, fc * 0.55), min(SR / 2 - 100, fc * 1.6)], btype="band", fs=SR, output="sos")
        if zi is None: zi = np.zeros((sos.shape[0], 2))
        y, zi = sosfilt(sos, x[i:i + blk], zi=zi)
        out[i:i + blk] = y
    tt = np.arange(n) / n
    e = np.where(tt < peak, (tt / peak) ** 2, ((1 - tt) / (1 - peak)) ** 1.5)
    return out * e / (np.abs(out).max() + 1e-9)

def tone(f, dur, decay, f_end=None):
    n = int(dur * SR); t = np.arange(n) / SR
    if f_end is None: ph = 2 * np.pi * f * t
    else:
        k = np.log(f_end / f) / dur
        ph = 2 * np.pi * f * (np.exp(k * t) - 1) / k
    return np.sin(ph) * np.exp(-t / decay)

def norm(x, g=1.0): return x / (np.abs(x).max() + 1e-9) * g

def make(kind):
    if kind == "swoosh": return norm(sweep_noise(0.32, 500, 3200, 1200, 0.55), 0.55)
    if kind == "whoosh": return norm(sweep_noise(0.5, 250, 2200, 700, 0.5), 0.6)
    if kind == "soft": return norm(sweep_noise(0.4, 300, 1500, 600, 0.5), 0.35)
    if kind == "swish": return norm(sweep_noise(0.25, 1500, 5000, 2500, 0.4), 0.35)
    if kind == "transition":
        w = sweep_noise(0.6, 200, 2600, 500, 0.62)
        sub = tone(90, 0.6, 0.25, 45) * np.minimum(1, np.arange(int(0.6 * SR)) / (0.3 * SR))
        return norm(w + 0.35 * sub, 0.8)
    if kind == "pop":
        p = tone(950, 0.12, 0.03, 320)
        c = hp(rng.normal(0, 1, int(0.006 * SR)), 2000) * np.linspace(1, 0, int(0.006 * SR))
        p[:len(c)] += 0.3 * c
        return norm(p, 0.55)
    if kind == "impact":
        n = int(0.7 * SR)
        b = tone(110, 0.7, 0.18, 42)
        nz = lp(rng.normal(0, 1, n), 900) * env_ar(n, 0.002, 0.06)
        p = np.zeros(n); pp = make("pop"); p[:len(pp)] = pp
        return norm(b + 0.5 * norm(nz) + 0.6 * p, 0.8)
    if kind == "stamp":
        n = int(0.4 * SR)
        b = tone(80, 0.4, 0.09, 50)
        nz = bp(rng.normal(0, 1, n), 300, 4000) * env_ar(n, 0.001, 0.03)
        return norm(b + 0.8 * norm(nz), 0.85)
    if kind == "ding":
        n = int(0.9 * SR); t = np.arange(n) / SR
        f = 1568
        x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / d) for m, a, d in [(1, 1, 0.35), (2.0, 0.35, 0.18), (2.76, 0.25, 0.12), (5.4, 0.12, 0.05)])
        x *= np.minimum(1, t / 0.002)
        return norm(x, 0.32)
    if kind == "tick":
        n = int(0.012 * SR)
        x = bp(rng.normal(0, 1, n), 2500, 6000) * np.exp(-np.arange(n) / (0.002 * SR))
        return norm(x, 0.22)
    if kind == "shine":
        n = int(0.9 * SR); t = np.arange(n) / SR
        x = np.zeros(n)
        for i, f in enumerate([2093, 2637, 3136, 3951, 4699]):
            st = int(i * 0.07 * SR)
            tt = t[:n - st]
            x[st:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.25) * np.minimum(1, tt / 0.01)
        x *= 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)
        return norm(x, 0.2)
    if kind == "coin":
        n = int(0.6 * SR); t = np.arange(n) / SR
        x = np.zeros(n)
        for st, f in [(0, 2400), (0.09, 3200)]:
            s0 = int(st * SR); tt = t[:n - s0]
            x[s0:] += (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2.7 * tt)) * np.exp(-tt / 0.12)
        return norm(x, 0.3)
    if kind == "rise":
        d = 0.8
        x = tone(300, d, 10, 1200) * np.linspace(0.2, 1, int(d * SR)) * np.linspace(1, 0, int(d * SR)) ** 0.3
        return norm(x + 0.3 * sweep_noise(d, 400, 3000, 3000, 0.95), 0.3)
    raise KeyError(kind)

GAIN = {"swoosh": 0.55, "whoosh": 0.6, "soft": 0.5, "swish": 0.45, "transition": 0.75, "pop": 0.55, "impact": 0.7,
        "stamp": 0.8, "ding": 0.5, "tick": 0.5, "shine": 0.55, "coin": 0.6, "rise": 0.5}

def sfx_track(total):
    ev = json.load(open(WORK + "sfx_events.json"))
    out = np.zeros(int(total * SR) + SR)
    cache = {}
    for t, kind, g, name in ev:
        if kind.startswith("ticks:"):
            dur = float(kind.split(":")[1])
            tk = make("tick")
            nt = int(dur / 0.055)
            for i in range(nt):
                u = i / max(1, nt)
                # ticks slow down as the count eases out
                tt = t + dur * (1 - (1 - u) ** (1 / 3)) if False else t + dur * (1 - (1 - u) ** 0.5) * 0.9
                s0 = int(tt * SR)
                out[s0:s0 + len(tk)] += tk * GAIN["tick"] * (0.7 + 0.3 * rng.random())
            continue
        if kind not in cache: cache[kind] = make(kind)
        x = cache[kind]
        # whooshes peak around the motion: start a bit earlier
        lead = {"swoosh": 0.08, "whoosh": 0.12, "soft": 0.1, "transition": 0.25, "swish": 0.05}.get(kind, 0.0)
        s0 = max(0, int((t - lead) * SR))
        seg = x[:len(out) - s0]
        out[s0:s0 + len(seg)] += seg * GAIN[kind] * g
    return out

if __name__ == "__main__":
    total = float(sys.argv[1])
    sfx = sfx_track(total)
    # gentle stereo-ish: write mono, mixed later
    sf.write(WORK + "sfx.wav", np.clip(sfx, -1, 1), SR)
    print("sfx peak", np.abs(sfx).max())
