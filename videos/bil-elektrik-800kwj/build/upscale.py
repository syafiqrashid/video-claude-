import json, subprocess, sys, numpy as np, onnxruntime as ort
P = "/home/user/video-claude-/videos/bil-elektrik-800kwj"
SRC = P + "/assets/source.mp4"
edl = json.load(open(P + "/build/edl.json"))["pieces"]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession("/tmp/claude-0/sr/sr.onnx", so, providers=["CPUExecutionProvider"])
W, H, OW, OH = 270, 494, 1080, 1976
import os; os.makedirs(P + "/assets/hq", exist_ok=True)
for i, p in enumerate(edl):
    out = f"{P}/assets/hq/p{i:02d}.mp4"
    if os.path.exists(out): continue
    st, du = p["src_in"], round(p["src_out"] - p["src_in"], 3)
    dec = subprocess.Popen(["ffmpeg","-v","error","-ss",str(st),"-i",SRC,"-t",str(du),"-vf","scale=270:494:flags=lanczos","-f","rawvideo","-pix_fmt","rgb24","-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{OW}x{OH}","-r","30","-i","-",
        "-ss",str(st),"-t",str(du),"-i",SRC,"-map","0:v","-map","1:a",
        "-vf","eq=contrast=1.05:saturation=1.12:gamma=1.02,colorbalance=rm=0.02:bm=-0.02",
        "-c:v","libx264","-crf","15","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",out+".tmp.mp4"], stdin=subprocess.PIPE)
    n = 0
    while True:
        b = dec.stdout.read(W*H*3)
        if len(b) < W*H*3: break
        x = np.frombuffer(b, np.uint8).reshape(H, W, 3).transpose(2,0,1)[None].astype(np.float32)/255
        y = sess.run(None, {"x": x})[0][0].clip(0,1)
        enc.stdin.write((y.transpose(1,2,0)*255+0.5).astype(np.uint8).tobytes()); n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    os.rename(out+".tmp.mp4", out)
    print(f"piece {i} done frames {n}", flush=True)
print("ALL DONE", flush=True)
