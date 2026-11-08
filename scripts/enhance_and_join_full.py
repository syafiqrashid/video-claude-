"""Join the four videos in script order and clean up the voice.

Full programme: opening (video 5, first clip) -> the four points in script
order (Manfaat Merdeka, Warisan Perjuangan, Patriotisme, Kesejahteraan) ->
closing (video 5, "Akhir kata" .. end card). Video 5 audio is already cleaned.

Voice chain per video (from each project's trimmed voice.wav):
  noise reduction (spectral gating, noise profile = quietest frames of the track)
  -> adaptive FFT denoise -> gentle gate in pauses
  -> high-pass / low-pass -> EQ (less mud, more presence) -> de-esser
  -> gentle compression -> loudness -14 LUFS, true peak -1.5 dB
Run from the repo root. Writes final/merdeka-penuh-HD.mp4.
"""
import subprocess, json
import numpy as np, soundfile as sf, noisereduce as nr

PARTS = [
    ("video2/output/manfaat-merdeka-HD.mp4", "video2/assets/voice.wav"),
    ("output/merdeka-warisan-perjuangan-HD.mp4", "merdeka/assets/voice.wav"),
    ("video3/output/patriotisme-HD.mp4", "video3/assets/voice.wav"),
    ("video4/output/kesejahteraan-HD.mp4", "video4/assets/voice.wav"),
]
W = "final/work/"
EQ = ("afftdn=nr=10:nf=-50:tn=1,"            # second, adaptive noise reduction pass
      "agate=range=0.3:threshold=0.012:ratio=1.6:attack=8:release=220,"   # soften residual noise in pauses
      "highpass=f=85,lowpass=f=14000,"
      "equalizer=f=250:t=q:w=1.1:g=-3,equalizer=f=3200:t=q:w=1.3:g=2.5,equalizer=f=9000:t=q:w=1:g=1,"
      "deesser=i=0.35,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=1,"
      "loudnorm=I=-14:TP=-1.5:LRA=6")

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def noise_floor(x, sr):
    f = int(0.02 * sr)
    e = np.array([np.sqrt(np.mean(x[i:i + f] ** 2)) for i in range(0, len(x) - f, f)])
    return 20 * np.log10(np.percentile(e, 5) + 1e-9)

report, segs = [], []
for i, (vid, voice) in enumerate(PARTS, 1):
    y, sr = sf.read(voice, always_2d=True)
    mono = y.mean(axis=1)
    # noise profile: the quietest 20 ms frames of this track (breaths/pauses)
    f = int(0.02 * sr)
    frames = [mono[k:k + f] for k in range(0, len(mono) - f, f)]
    rms = np.array([np.sqrt(np.mean(fr ** 2)) for fr in frames])
    quiet = np.concatenate([frames[k] for k in np.argsort(rms)[: max(25, len(frames) // 12)]])
    clean = nr.reduce_noise(y=mono, sr=sr, y_noise=quiet, stationary=True, prop_decrease=0.9,
                            n_std_thresh_stationary=1.5, freq_mask_smooth_hz=400, time_mask_smooth_ms=60)
    sf.write(W + f"nr{i}.wav", clean, sr)
    out = W + f"voice{i}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", W + f"nr{i}.wav", "-af", EQ + ",aresample=48000",
                    "-ac", "2", out], check=True)
    o, _ = sf.read(out)
    report.append({"part": i, "noise_floor_before_db": round(noise_floor(mono, sr), 1),
                   "noise_floor_after_db": round(noise_floor(o.mean(axis=1), 48000), 1)})
    seg = W + f"part{i}.mp4"
    d = dur(vid)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", out, "-map", "0:v", "-map", "1:a",
                    "-af", f"apad,atrim=0:{d}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(d), seg], check=True)
    segs.append(seg)

# opening / closing cut from the finished video 5 at its clip boundary (frame 720)
V5, CUT = "video5/output/jiwa-merdeka-HD.mp4", 24.0
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", V5, "-t", str(CUT), "-c:v", "libx264", "-crf", "16", "-preset", "fast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", W + "opening.mp4"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(CUT), "-i", V5, "-c:v", "libx264", "-crf", "16", "-preset", "fast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", W + "closing.mp4"], check=True)
segs = [W + "opening.mp4"] + segs + [W + "closing.mp4"]

with open(W + "list.txt", "w") as fh:
    fh.writelines(f"file '{s.split('/')[-1]}'\n" for s in segs)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", W + "list.txt",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "final/merdeka-penuh-HD.mp4"], check=True)
print(json.dumps(report, indent=1))
