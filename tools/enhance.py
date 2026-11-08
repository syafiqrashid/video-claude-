import sys, numpy as np, soundfile as sf, noisereduce as nr
a, sr = sf.read(sys.argv[1], dtype="float32")
noise = a[int(0.0*sr):int(0.30*sr)]   # leading room tone
red = nr.reduce_noise(y=a, sr=sr, y_noise=noise if len(noise)>sr*0.2 else None, stationary=True,
                      prop_decrease=0.75, n_fft=2048, freq_mask_smooth_hz=300, time_mask_smooth_ms=60)
sf.write(sys.argv[2], red, sr, subtype="PCM_24")
