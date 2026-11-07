import subprocess, sys, time
import numpy as np, torch

src, model_path, out = sys.argv[1:4]
W, H = 720, 1280
torch.set_num_threads(4)
model = torch.jit.freeze(torch.jit.load(model_path).eval())

# HLG HDR (iPhone) -> SDR bt709, scaled to 720x1280
vf = (f"zscale=w={W}:h={H}:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
      "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=pc,format=rgb24")
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-map", "0:v:0", "-vf", vf,
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE, bufsize=10**7)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", "60", "-i", "-", "-i", src,
                        "-map", "0:v", "-map", "1:a:0", "-c:a", "aac", "-b:a", "160k",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-movflags", "+faststart", "-shortest", out],
                       stdin=subprocess.PIPE)

rec, dr, fsize, n, t0 = [None] * 4, torch.tensor([0.4]), W * H * 3, 0, time.time()
with torch.no_grad():
    while True:
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
        full = torch.from_numpy(img).permute(2, 0, 1)[None]
        fgr, pha, *rec = model(full, *rec, dr)
        w = ((pha - 0.6) / 0.4).clamp(0, 1)  # use clean predicted fg at soft edges (removes wall spill)
        o = (pha * (w * full + (1 - w) * fgr)).clamp(0, 1)[0].permute(1, 2, 0).numpy()
        enc.stdin.write((o * 255 + 0.5).astype(np.uint8).tobytes())
        n += 1
        if n % 50 == 0:
            print(f"{n} frames, {n / (time.time() - t0):.1f} fps", flush=True)
enc.stdin.close()
enc.wait()
print("done", n)
