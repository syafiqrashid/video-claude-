# Generates a light, upbeat 30 s background track + transition whooshes (no external samples).
import numpy as np, wave, sys
SR = 44100; DUR = 30.0; BPM = 112; beat = 60 / BPM
t = np.arange(int(SR * DUR)) / SR
mix = np.zeros_like(t)
def note(f, start, length, amp, kind='pluck'):
    i0 = int(start * SR); n = int(length * SR); i1 = min(i0 + n, len(t))
    if i0 >= len(t): return
    tt = np.arange(i1 - i0) / SR
    if kind == 'pluck':
        s = (np.sin(2*np.pi*f*tt) + .4*np.sin(4*np.pi*f*tt) + .15*np.sin(6*np.pi*f*tt)) * np.exp(-tt*6)
    elif kind == 'pad':
        s = (np.sin(2*np.pi*f*tt) + .5*np.sin(2*np.pi*f*1.005*tt)) * np.minimum(1, tt/.3) * np.minimum(1, (length-tt)/.3)
    elif kind == 'bass':
        s = np.sin(2*np.pi*f*tt) * np.exp(-tt*3)
    mix[i0:i1] += amp * s
mid = lambda m: 440 * 2 ** ((m - 69) / 12)
prog = [[60,64,67],[67,71,74],[69,72,76],[65,69,72]]   # C G Am F
bar = beat * 4; nb = int(DUR / bar) + 1
for b in range(nb):
    ch = prog[b % 4]; t0 = b * bar
    for k in range(3): note(mid(ch[k]-12), t0, bar, .05, 'pad')
    note(mid(ch[0]-24), t0, beat*1.8, .22, 'bass'); note(mid(ch[0]-24), t0+beat*2, beat*1.8, .2, 'bass')
    arp = [ch[0], ch[1], ch[2], ch[1]+12, ch[2], ch[1], ch[0]+12, ch[2]]
    for k, m in enumerate(arp): note(mid(m), t0 + k*beat/2, beat*.9, .09)
# drums
rng = np.random.default_rng(1)
for k in range(int(DUR / beat)):
    i0 = int(k*beat*SR); n = int(.25*SR); tt = np.arange(n)/SR
    seg = slice(i0, min(i0+n, len(t))); L = seg.stop - seg.start
    kick = np.sin(2*np.pi*(50 + 90*np.exp(-tt*30))*tt) * np.exp(-tt*12)
    mix[seg] += .45 * kick[:L]
    if k % 2: # clap-ish snare
        sn = rng.normal(size=n) * np.exp(-tt*18); mix[seg] += .1 * sn[:L]
    h0 = int((k*beat + beat/2)*SR); hn = int(.05*SR)
    if h0 + hn < len(t): mix[h0:h0+hn] += .04 * rng.normal(size=hn) * np.exp(-np.arange(hn)/SR*80)
# whooshes at scene changes
for ts in [4, 9, 16, 22, 27]:
    n = int(.6*SR); i0 = int((ts-.35)*SR); tt = np.arange(n)/SR
    nz = rng.normal(size=n); nz = np.convolve(nz, np.ones(12)/12, 'same')
    env = np.sin(np.pi*tt/.6)**2
    mix[i0:i0+n] += .35 * nz * env
# fade in/out + normalise
env = np.minimum(1, t/0.5) * np.minimum(1, (DUR - t)/1.5)
mix *= env; mix /= np.max(np.abs(mix)) * 1.15
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
