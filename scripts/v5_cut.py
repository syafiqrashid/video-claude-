"""Video 5 step 1: join both clips, drop the repeated takes, shorten long pauses.

Clip 1 (IMG_2863): intro + kemerdekaan statement, then 4 takes of
"Hari ini kita berdiri megah sebagai rakyat Malaysia" -> keep only the last,
complete take. Clip 2 (IMG_2864): closing, no retakes.
Pauses longer than MAX_GAP are cut down to KEEP_GAP (jump cut; the composition
punches in/out on each cut to hide it). Writes video5/work/edit.mov + edl.json.
Run from the repo root.
"""
import json, re, subprocess

RAW = "video5/raw/"
KEEP = [  # (clip, start, end) in raw seconds
    ("clip2863.mov", 2.15, 18.75),   # Assalamualaikum ... masa depan yang lebih baik
    ("clip2863.mov", 35.55, 44.80),  # last take: Hari ini kita berdiri megah ... terus melangkah ke depan
    ("clip2864.mov", 1.35, 29.75),   # Akhir kata ... Sekian terima kasih daripada saya
]
MAX_GAP, KEEP_GAP = 0.48, 0.26

def silences(path):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.25",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    s = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    e = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(s, e))

segs = []
for clip, a, b in KEEP:
    cur = a
    for s, e in silences(RAW + clip):
        if e <= a or s >= b or e - s <= MAX_GAP:
            continue
        s, e = max(s, a), min(e, b)
        if s - cur > 0.2:
            segs.append((clip, round(cur, 3), round(s + KEEP_GAP / 2, 3)))
        cur = e - KEEP_GAP / 2
    if b - cur > 0.2:
        segs.append((clip, round(cur, 3), b))

edl, t = [], 0.0
for clip, a, b in segs:
    edl.append({"clip": clip, "raw_start": a, "raw_end": b, "out_start": round(t, 3)})
    t += b - a
json.dump({"segments": edl, "duration": round(t, 3)}, open("video5/work/edl.json", "w"), indent=1)

inputs, parts, labels = [], [], []
clips = sorted({c for c, _, _ in segs})
for c in clips:
    inputs += ["-i", RAW + c]
for i, (clip, a, b) in enumerate(segs):
    k = clips.index(clip)
    d = b - a
    parts.append(f"[{k}:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
    parts.append(f"[{k}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d - 0.015:.3f}:d=0.015[a{i}]")
    labels.append(f"[v{i}][a{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le",
                "video5/work/edit.mov"], check=True)
print(len(segs), "segments, duration", round(t, 2))
for s in edl: print(s)
