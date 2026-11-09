# Assemble opening (HyperFrames) + content 1-6 (unchanged) + closing (HyperFrames); mix audio.
import numpy as np, soundfile as sf, subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import audio as A

SC = "/tmp/claude-0/-home-user-video-claude-/2a734288-29af-5c47-8d50-5a13f3989741/scratchpad/"
W, D, HF = SC + "work/", SC + "dl2/", SC + "hf/"
SR = 48000
OUT_W = int(os.environ.get("OUT_W", 540)); OUT_H = OUT_W * 16 // 9
OPEN_D, CONTENT_D, CLOSE_D = 13.3, 177.7, 8.9
T_CONTENT, T_CLOSE = OPEN_D, OPEN_D + CONTENT_D
TOTAL = T_CLOSE + CLOSE_D
OUT = sys.argv[1]
CHUNKS = os.environ.get("CHUNKS", "chunks2")
SUFFIX = os.environ.get("HF_SUFFIX", "")
CRF = os.environ.get("CRF", "23"); PRESET = os.environ.get("PRESET", "veryfast"); ABR = os.environ.get("ABR", "160k")

def run(*a): subprocess.run(list(a), check=True)

# ---------- talking-head voice: denoise, EQ, compress, -16 LUFS (same target as content VO)
CHAIN = ("highpass=f=85,afftdn=nr=14:nf=-55:tn=1,equalizer=f=250:t=q:w=1.2:g=-2,"
         "equalizer=f=3500:t=q:w=1.5:g=2.5,equalizer=f=9000:t=h:w=1:g=1.5,deesser=i=0.3,"
         "acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=3,loudnorm=I=-16:TP=-1.5:LRA=8")
for p in ("opening", "closing"):
    run("ffmpeg", "-y", "-loglevel", "error", "-i", D + f"th_{p}.mov", "-vn", "-ac", "1", "-ar", str(SR), "-af", CHAIN, W + f"th_{p}_vo.wav")

n = int(TOTAL * SR) + SR
voice = np.zeros(n); sfx = np.zeros(n)
def place(buf, x, t, g=1.0):
    s0 = int(t * SR); x = x[: len(buf) - s0]; buf[s0:s0 + len(x)] += x * g

place(voice, sf.read(W + "th_opening_vo.wav")[0], 0.0)
cv = sf.read(W + "vo_master.wav")[0]; place(voice, cv[: int(CONTENT_D * SR)], T_CONTENT)
place(voice, sf.read(W + "th_closing_vo.wav")[0], T_CLOSE)

cs = sf.read(W + "sfx.wav")[0]
fade = np.ones(int(CONTENT_D * SR)); fade[-int(0.3 * SR):] = np.linspace(1, 0, int(0.3 * SR))
place(sfx, cs[: int(CONTENT_D * SR)] * fade, T_CONTENT)

cache = {}
def fx(kind, t, g=1.0):
    if kind not in cache: cache[kind] = A.make(kind)
    lead = {"swoosh": 0.08, "whoosh": 0.12, "soft": 0.1, "transition": 0.25, "swish": 0.05}.get(kind, 0.0)
    place(sfx, cache[kind], max(0, t - lead), A.GAIN[kind] * g)

# opening events (seconds, film time) — match the GSAP timings in hf/film
fx("whoosh", 1.42); fx("swoosh", 2.2, 0.7); fx("pop", 2.32, 0.7)
fx("impact", 5.66, 0.8); fx("pop", 6.74); fx("ding", 7.4, 0.8)
fx("transition", 9.1); fx("swish", 9.22, 0.7)
for i in range(6): fx("pop", 9.1 + 0.42 + i * 0.17, 0.75)
fx("ding", 11.38, 0.6)
fx("whoosh", 9.1 + 3.38, 1.1); fx("rise", 9.1 + 3.38, 0.7)
# closing events
c = T_CLOSE
fx("transition", c + 0.05, 0.8); fx("shine", c, 0.6)
for t in (2.64, 3.2, 3.92): fx("pop", c + t); fx("ding", c + t + 0.3, 0.6)
fx("impact", c + 4.46, 0.7)
fx("transition", c + 5.6, 0.8); fx("pop", c + 5.9); fx("shine", c + 6.15, 0.7)

sf.write(W + "full_voice.wav", np.clip(voice, -1, 1), SR)
sf.write(W + "full_sfx.wav", np.clip(sfx, -1, 1), SR)

# ---------- background music: Bahtera Merdeka (from the reference), looped to length
REF = "/root/.claude/uploads/2a734288-29af-5c47-8d50-5a13f3989741/d4e67a0d-v0f025gc0000cc8cacrc77u4ngitd9hg.mp4"
run("ffmpeg", "-y", "-loglevel", "error", "-ss", "1.64", "-to", "152.75", "-i", REF, "-vn", "-ac", "2", "-ar", str(SR), W + "bgm_a.wav")
run("ffmpeg", "-y", "-loglevel", "error", "-i", W + "bgm_a.wav", "-ss", "6", "-i", W + "bgm_a.wav", "-filter_complex",
    f"[0][1]acrossfade=d=4:c1=tri:c2=tri,atrim=0:{TOTAL},afade=t=in:d=0.8,afade=t=out:st={TOTAL - 3.5}:d=3.5,loudnorm=I=-16:TP=-2:LRA=11",
    "-ar", str(SR), W + "full_bgm.wav")

run("ffmpeg", "-y", "-loglevel", "error", "-i", W + "full_voice.wav", "-i", W + "full_bgm.wav", "-i", W + "full_sfx.wav", "-filter_complex",
    "[0]aformat=channel_layouts=mono,asplit=2[vo][vosc];[1]volume=-12dB[bg];[vosc]pan=stereo|c0=c0|c1=c0[sc];"
    "[bg][sc]sidechaincompress=threshold=0.015:ratio=5:attack=25:release=550:makeup=1[bgd];"
    "[vo]pan=stereo|c0=c0|c1=c0[vos];[2]volume=0.75,pan=stereo|c0=c0|c1=c0[fx];"
    f"[vos][bgd][fx]amix=inputs=3:normalize=0:duration=longest,atrim=0:{TOTAL},alimiter=limit=0.94:level=disabled[out]",
    "-map", "[out]", "-ar", str(SR), W + "full_mix.wav")

# ---------- picture
with open(W + "concat2.txt", "w") as f:
    names = os.environ.get("CHUNK_FILES", "c0 c1 c2 c3").split()
    for nm in names: f.write(f"file '{CHUNKS}/{nm}.mp4'\n")
run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", W + "concat2.txt", "-i", HF + f"opening_render{SUFFIX}.mp4",
    "-i", HF + f"closing_render{SUFFIX}.mp4", "-i", W + "full_mix.wav", "-filter_complex",
    f"[1:v]scale={OUT_W}:{OUT_H}:flags=lanczos,fps=30,setsar=1,trim=0:{OPEN_D},setpts=PTS-STARTPTS[o];"
    f"[0:v]scale={OUT_W}:{OUT_H}:flags=lanczos,fps=30,setsar=1,trim=0:{CONTENT_D},setpts=PTS-STARTPTS[m];"
    f"[2:v]scale={OUT_W}:{OUT_H}:flags=lanczos,fps=30,setsar=1,trim=0:{CLOSE_D},setpts=PTS-STARTPTS[c];"
    "[o][m][c]concat=n=3:v=1:a=0[v]",
    "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-profile:v", "high", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", ABR, "-shortest", "-movflags", "+faststart", OUT)
print("done", OUT, TOTAL)
