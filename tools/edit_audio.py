# Compress awkward pauses; write edited wav + cut map (json)
import sys, json, numpy as np, soundfile as sf
src, silf, transf, out_wav, out_map = sys.argv[1:6]
a, sr = sf.read(src, dtype="float32")
dur = len(a)/sr
sil = [tuple(map(float,l.split())) for l in open(silf) if len(l.split())==2]
words = [w for s in json.load(open(transf)) for w in s["words"]]
seg_starts = [s["start"] for s in json.load(open(transf))]
SECTION = [2.48, 33.05, 65.82, 101.12, 130.88, 156.88]   # "Yang pertama..keenam"
PAD = 0.10
cuts = []  # (remove_start, remove_end)
for s0, s1 in sil:
    L = s1 - s0
    if s0 < 0.05:                       # leading silence
        target = 0.35
    elif s1 > dur - 0.2:                # trailing
        target = 1.0
    elif any(abs(s1 - t) < 0.6 for t in SECTION):
        target = 0.85                    # breath between sections
    elif any(abs(s1 - t) < 0.5 for t in seg_starts):
        target = 0.42                    # sentence boundary
    else:
        target = 0.26                    # mid-sentence hesitation
    if L > target + 0.08:
        # keep PAD-ish on both sides, remove the middle
        keep_l = min(target/2, PAD + 0.05); keep_r = target - keep_l
        cuts.append((s0 + keep_l, s1 - keep_r))
# manual cuts: retakes / false starts found by windowed re-transcription
MANUAL = [(43.92, 44.53),   # 'pe-' false start before 'penyelenggaraan'
          (78.92, 82.30),   # 1st take 'disasarkan menerima peluang pembelajaran' -> keep retake
          (135.28, 136.24), # 'Bagi me-' false start
          (176.56, 177.24)] # 'Pembiar-' false start
allc = sorted(cuts + MANUAL); cuts = []
for c in allc:
    if cuts and c[0] <= cuts[-1][1] + 0.02: cuts[-1] = (cuts[-1][0], max(cuts[-1][1], c[1]))
    else: cuts.append(c)
# build keep intervals
keeps, t = [], 0.0
for c0, c1 in cuts:
    keeps.append((t, c0)); t = c1
keeps.append((t, dur))
XF = int(0.012*sr)
outp = []; mp = []; newt = 0.0
for k0, k1 in keeps:
    seg = a[int(k0*sr):int(k1*sr)].copy()
    if len(seg) > 2*XF:
        ramp = np.linspace(0,1,XF,dtype="float32")
        seg[:XF] *= ramp; seg[-XF:] *= ramp[::-1]
    outp.append(seg); mp.append({"src":[k0,k1],"dst":[newt,newt+len(seg)/sr]}); newt += len(seg)/sr
sf.write(out_wav, np.concatenate(outp), sr, subtype="PCM_24")
removed = sum(c1-c0 for c0,c1 in cuts)
json.dump({"segments":mp,"cuts":cuts}, open(out_map,"w"), indent=1)
print(f"cuts={len(cuts)} removed={removed:.2f}s  {dur:.2f}s -> {newt:.2f}s")
for c0,c1 in cuts: print(f"  cut {c0:7.2f}-{c1:7.2f} ({c1-c0:.2f}s)")
