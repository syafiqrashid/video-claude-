"""Video 4 (kesejahteraan): remove awkward pauses and repeated/failed takes.

Detects silences with ffmpeg, shortens every pause, and writes:
  assets/voice.wav        - edited, normalized voice track
  assets/cut_map.json     - kept raw segments + their offsets in the edited track
"""
import json, re, subprocess, sys

RAW = "video4/raw/voice-raw-v2.m4a"   # re-recorded take that includes frame 4
OUT = "video4/assets/voice.wav"
MAP = "video4/raw/cut_map.json"
START, END = 7.20, 58.45          # trim dead air before "Yang keempat" and after the last word
REMOVE = []                       # retakes are cut exactly with EXACT_REMOVE below
# exact cuts (no padding): two failed takes of "dan perkhidmatan yang memberi..."
# and the first, shorter take of "Kemajuan negara bukan sekadar diukur..."
EXACT_REMOVE = []   # the re-recorded take has no repeated phrases
SENTENCE_BREAKS = [17.6, 31.2, 41.9]    # pauses between storyboard frames
SHORT_GAP, LONG_GAP = 0.20, 0.45  # max pause kept inside / between frames

log = subprocess.run(["ffmpeg", "-hide_banner", "-i", RAW, "-af",
                      "silencedetect=noise=-38dB:d=0.22", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
sil = [(s, e) for s, e in zip(starts, ends) if e > START and s < END]
# treat removed retakes as silence so they are cut like a pause
sil = sorted(sil + REMOVE)
sil2 = []
for s_, e_ in sil:
    if sil2 and s_ <= sil2[-1][1] + 0.05:
        sil2[-1] = (sil2[-1][0], max(e_, sil2[-1][1]))
    else:
        sil2.append((s_, e_))
sil = sil2
# merge silences separated by a tiny blip (breath) < 0.3s
merged = []
for s, e in sil:
    if merged and s - merged[-1][1] < 0.3:
        merged[-1] = (merged[-1][0], e)
    else:
        merged.append((s, e))

segs, cur = [], START
for s, e in merged:
    s, e = max(s, START), min(e, END)
    if s <= START + 0.01:
        cur = max(cur, e - 0.10)
        continue
    long_ = any(s - 0.6 <= b <= e + 0.6 for b in SENTENCE_BREAKS)
    keep = LONG_GAP if long_ else SHORT_GAP
    if e - s <= keep:
        continue
    segs.append((cur, s + keep / 2))
    cur = e - keep / 2
segs.append((cur, END))
# subtract the exact removals
cut = []
for a, b in segs:
    pieces = [(a, b)]
    for ra, rb in EXACT_REMOVE:
        nxt = []
        for x, y in pieces:
            if rb <= x or ra >= y:
                nxt.append((x, y))
                continue
            if x < ra: nxt.append((x, ra))
            if rb < y: nxt.append((rb, y))
        pieces = nxt
    cut += [p for p in pieces if p[1] - p[0] > 0.03]
segs = cut

out, t = [], 0.0
for a, b in segs:
    out.append({"raw_start": round(a, 3), "raw_end": round(b, 3), "out_start": round(t, 3)})
    t += b - a
print(json.dumps(out, indent=1)); print("edited duration", round(t, 3), file=sys.stderr)

parts, labels = [], []
for i, (a, b) in enumerate(segs):
    d = b - a
    parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,"
                 f"afade=t=out:st={d-0.02:.3f}:d=0.02[s{i}]")
    labels.append(f"[s{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=0:a=1," \
     "highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80," \
     "loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", RAW, "-filter_complex", fc,
                "-map", "[out]", "-ac", "2", OUT], check=True)
json.dump({"segments": out, "duration": round(t, 3)}, open(MAP, "w"), indent=1)
