# Cut talking-head clips: keep chosen takes, compress pauses, alternate punch-in zoom.
import json, numpy as np, soundfile as sf, subprocess, sys
D = "/tmp/claude-0/-home-user-video-claude-/2a734288-29af-5c47-8d50-5a13f3989741/scratchpad/dl2/"
SR = 48000

def load(c):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", D + f"sdr_{c}.mov", "-ac", "1", "-ar", str(SR), D + f"{c}48.wav"], check=True)
    a, _ = sf.read(D + f"{c}48.wav")
    hop = int(0.01 * SR)
    db = np.array([20 * np.log10(np.sqrt(np.mean(a[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(a) - hop, hop)])
    words = [dict(s=w["s"], e=w["e"], w=w["w"].strip()) for s in json.load(open(D + f"tr_{c}.json")) for w in s["words"]]
    return db, words

FIX = {"Ihtia": "ikhtiar", "seber": "serba", "kerajaan": "Kerajaan"}

# (clip, first word start, last word end, word replacements)
PARTS = {
    "opening": [("clipA", 0.0, 2.08), ("clipA", 8.28, 14.04), ("clipB", 1.18, 5.08)],
    "closing": [("clipB", 7.44, 12.70)],
}
TH = -42  # dB speech threshold

def refine(db, t0, t1):
    i0 = int(t0 * 100); i1 = int(t1 * 100)
    # start: walk back to silence (max 0.3s)
    j = i0
    while j > max(0, i0 - 30) and db[j - 1] > TH: j -= 1
    k = i1
    while k < min(len(db) - 1, i1 + 40) and db[k] > TH: k += 1
    return max(0, j / 100 - 0.05), k / 100 + 0.12

def pauses(db, t0, t1, minlen=0.28):
    out = []; i = int(t0 * 100); n = int(t1 * 100)
    while i < n:
        if db[i] < TH:
            j = i
            while j < n and db[j] < TH: j += 1
            if (j - i) / 100 >= minlen: out.append((i / 100, j / 100))
            i = j
        else: i += 1
    return out

result = {}
for part, segs in PARTS.items():
    pieces = []  # (clip, a, b)
    words_out = []
    for c, w0, w1 in segs:
        db, words = load(c)
        a, b = refine(db, w0, w1)
        cur = a
        for p0, p1 in pauses(db, a + 0.1, b - 0.1):
            keep_pre, keep_post = 0.12, 0.08
            if (p1 - keep_post) - (p0 + keep_pre) < 0.15: continue
            pieces.append((c, cur, p0 + keep_pre)); cur = p1 - keep_post
        pieces.append((c, cur, b))
        ws = [w for w in words if w["s"] >= w0 - 0.05 and w["e"] <= w1 + 0.05]
        for w in ws:
            w = dict(w, clip=c); w["w"] = FIX.get(w["w"].rstrip(".,"), w["w"].rstrip(".,")) + (w["w"][-1] if w["w"][-1] in ".," else "")
            words_out.append(w)
    # build new timeline
    t = 0.0; mp = []
    for c, a, b in pieces:
        mp.append((c, a, b, t)); t += b - a
    def remap(c, x):
        for cc, a, b, n0 in mp:
            if cc == c and a - 0.02 <= x <= b + 0.02: return n0 + min(max(x, a), b) - a
        best = min((abs(x - a), n0) for cc, a, b, n0 in mp if cc == c)
        return best[1]
    nw = [dict(w=w["w"], s=round(remap(w["clip"], w["s"]), 3), e=round(remap(w["clip"], w["e"]), 3)) for w in words_out]
    # zoom per "sentence" segment: alternate 1.0 / 1.14 on each source segment change
    seg_bounds = []; t = 0.0; zi = 0; last = None
    for c, a, b in pieces:
        zi += 1
        seg_bounds.append(dict(c=c, a=round(a, 3), b=round(b, 3), t=round(t, 3), zoom=1.0 if zi % 2 else 1.14)); t += b - a
    result[part] = dict(pieces=seg_bounds, words=nw, dur=round(t, 3))
    print(part, "dur", round(t, 2), " ".join(w["w"] for w in nw))
    for p in seg_bounds: print("   ", p)
json.dump(result, open(D + "th_edl.json", "w"), indent=1)

# render footage per part
for part, r in result.items():
    inputs = []; fc = []; idx = {}
    for c in ("clipA", "clipB"):
        idx[c] = len(inputs) // 2; inputs += ["-i", D + f"sdr_{c}.mov"]
    vlab = []; alab = []
    for i, p in enumerate(r["pieces"]):
        z = p["zoom"]; ii = idx[p["c"]]
        cw, ch = int(1080 / z) // 2 * 2, int(1920 / z) // 2 * 2
        # punch-in centred slightly above middle (face)
        fc.append(f"[{ii}:v]trim={p['a']}:{p['b']},setpts=PTS-STARTPTS,crop={cw}:{ch}:(iw-{cw})/2:(ih-{ch})*0.38,scale=1080:1920,setsar=1[v{i}]")
        fc.append(f"[{ii}:a]atrim={p['a']}:{p['b']},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={p['b']-p['a']-0.012:.3f}:d=0.012[a{i}]")
        vlab.append(f"[v{i}][a{i}]")
    fc.append("".join(vlab) + f"concat=n={len(vlab)}:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", "30", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1",
                    D + f"th_{part}.mov"], check=True)
    print("rendered", part)
