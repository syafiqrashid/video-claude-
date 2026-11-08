"""Video 5 step 4: clean up the voice from the edited cut.

Noise profile per source clip = its own silent lead-in (room tone), then
spectral-gating noise reduction, an adaptive FFT denoise pass, gentle pause
gate, EQ (less boxiness, more presence/air), de-esser, compression and
loudness -14 LUFS / -1.5 dBTP. Writes video5/work/voice.wav.
"""
import json, subprocess, numpy as np, soundfile as sf, noisereduce as nr

edl = json.load(open("video5/work/edl.json"))["segments"]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video5/work/edit.mov", "-ac", "1", "-ar", "48000", "video5/work/edit_mono.wav"], check=True)
y, sr = sf.read("video5/work/edit_mono.wav")
ROOM = {"clip2863.mov": (0.3, 2.1), "clip2864.mov": (0.1, 1.3)}   # silent lead-ins in the raw clips
out = np.zeros_like(y)
for clip in ROOM:
    a, b = ROOM[clip]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", f"video5/raw/{clip}", "-ac", "1", "-ar", "48000",
                    "video5/work/room.wav"], check=True)
    noise, _ = sf.read("video5/work/room.wav")
    clean = nr.reduce_noise(y=y, sr=sr, y_noise=noise, stationary=True, prop_decrease=0.9, n_std_thresh_stationary=1.5,
                            freq_mask_smooth_hz=400, time_mask_smooth_ms=60)
    for s in edl:
        if s["clip"] != clip:
            continue
        i0 = int(s["out_start"] * sr); i1 = int((s["out_start"] + s["raw_end"] - s["raw_start"]) * sr)
        out[i0:i1] = clean[i0:i1]
sf.write("video5/work/voice_nr.wav", out, sr)
CHAIN = ("afftdn=nr=10:nf=-50:tn=1,agate=range=0.3:threshold=0.012:ratio=1.6:attack=8:release=220,"
         "highpass=f=80,lowpass=f=15000,equalizer=f=320:t=q:w=1.2:g=-3.5,equalizer=f=3500:t=q:w=1.2:g=3,"
         "equalizer=f=10000:t=q:w=1:g=1.5,deesser=i=0.35,"
         "acompressor=threshold=-22dB:ratio=2.8:attack=8:release=120:makeup=1,loudnorm=I=-14:TP=-1.5:LRA=6")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video5/work/voice_nr.wav", "-af", CHAIN + ",aresample=48000", "-ac", "2",
                "video5/work/voice.wav"], check=True)

def snr(p):
    x, r = sf.read(p, always_2d=True); x = x.mean(1); f = int(.02 * r)
    e = np.array([np.sqrt(np.mean(x[i:i + f] ** 2)) for i in range(0, len(x) - f, f)]); d = 20 * np.log10(e + 1e-9)
    return np.percentile(d, 90) - np.percentile(d, 5)
print("speech-to-noise before %.1f dB, after %.1f dB" % (snr("video5/work/edit_mono.wav"), snr("video5/work/voice.wav")))
