"""Video 5 step 2: person alpha matte with Robust Video Matting (ONNX, CPU).

Reads video5/work/edit.mov, runs RVM at 540x960 (recurrent state keeps the
matte stable between frames), writes the alpha as a lossless grey video
video5/work/alpha.mkv at 1080x1920. Model path is passed as argv[1].
"""
import subprocess, sys, numpy as np, onnxruntime as ort

MODEL = sys.argv[1]
W, H, w, h = 1080, 1920, 540, 960
sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
ds = np.array([0.45], np.float32)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", "video5/work/edit.mov", "-vf", f"scale={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
                        "-r", "30", "-i", "-", "-vf", f"scale={W}:{H}:flags=bicubic", "-c:v", "ffv1",
                        "-pix_fmt", "gray", "video5/work/alpha.mkv"], stdin=subprocess.PIPE)
n = 0
while True:
    buf = dec.stdout.read(w * h * 3)
    if len(buf) < w * h * 3:
        break
    src = np.frombuffer(buf, np.uint8).reshape(h, w, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255
    fgr, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                     "downsample_ratio": ds})
    enc.stdin.write((np.clip(pha[0, 0], 0, 1) * 255).astype(np.uint8).tobytes())
    n += 1
    if n % 150 == 0:
        print(n, flush=True)
enc.stdin.close(); enc.wait()
print("frames", n)
