# Synthesize SFX and place them on animation events -> sfx track (48k stereo wav)
# usage: python3 tools/sfx.py data/events.json out_sfx.wav [sfx_dir]
import sys, json, os, numpy as np, soundfile as sf
SR = 48000
rng = np.random.default_rng(7)
def t_(d): return np.arange(int(d*SR))/SR
def env(n, a, r, curve=4):
    x = np.ones(n); na = max(1,int(a*SR)); x[:na] = np.linspace(0,1,na)**2
    tail = np.linspace(0,1,n-na); x[na:] = np.exp(-curve*tail) * (1-tail)
    return x
def bp_noise(n, f_lo, f_hi):  # time-varying band-pass via FFT on overlapping blocks
    out = np.zeros(n); B = 2048; H = B//2; win = np.hanning(B)
    noise = rng.standard_normal(n + B)
    for i in range(0, n, H):
        seg = noise[i:i+B] * win; F = np.fft.rfft(seg); fr = np.fft.rfftfreq(B, 1/SR)
        p = i/max(1,n); lo = f_lo[0]+(f_lo[1]-f_lo[0])*p; hi = f_hi[0]+(f_hi[1]-f_hi[0])*p
        F *= np.exp(-0.5*((np.log(fr+1)-np.log((lo+hi)/2))/(np.log(hi/lo)/2+1e-6))**2)
        o = np.fft.irfft(F); e = min(n, i+B); out[i:e] += o[:e-i]
    return out/ (np.abs(out).max()+1e-9)
def norm(x, g=1.0): return x/(np.abs(x).max()+1e-9)*g
def reverb(x, decay=0.35, mix=0.25):
    ir_n = int(decay*SR*2); ir = rng.standard_normal(ir_n)*np.exp(-np.arange(ir_n)/(decay*SR)); ir/=np.abs(ir).sum()/8
    y = np.convolve(x, ir)[:len(x)+ir_n]; y = np.pad(y,(0,len(x)+ir_n-len(y))); xx = np.pad(x,(0,ir_n)); return xx*(1-mix)+norm(y,np.abs(x).max())*mix
S = {}
# whoosh: band sweep up then down, swell
n = int(0.7*SR); w = bp_noise(n, (300,1800), (1500,6000)); S['whoosh'] = norm(w*env(n,0.38,0.32,3),0.9)
n = int(0.4*SR); w = bp_noise(n, (600,2500), (2500,8000)); S['swoosh'] = norm(w*env(n,0.15,0.25,4),0.7)
# impact: pitch-dropping sub + noise thump + tail
t = t_(1.2); f = 90*np.exp(-t*3)+38; ph = 2*np.pi*np.cumsum(f)/SR
imp = np.sin(ph)*np.exp(-t*3.2) + 0.5*bp_noise(len(t),(80,200),(400,1200))*np.exp(-t*14)
S['impact'] = norm(reverb(imp,0.5,0.3),0.95)
# pop: quick upward chirp + click
t = t_(0.12); f = 380+1400*t/0.12; pop = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*38)
pop[:60] += rng.standard_normal(60)*0.3; S['pop'] = norm(pop,0.8)
t = t_(0.1); f = 600+900*t/0.1; S['softpop'] = norm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*45),0.6)
# ding (check): bell partials
t = t_(0.6); d = sum(a*np.sin(2*np.pi*f*t)*np.exp(-t*k) for f,a,k in [(1568,1,7),(2352,.5,9),(3136,.25,12),(4704,.12,16)])
S['ding'] = norm(reverb(d*np.minimum(1,t*400),0.3,0.2),0.6)
# tick
t = t_(0.025); S['tick'] = norm(np.sin(2*np.pi*2600*t)*np.exp(-t*260)+0.2*rng.standard_normal(len(t))*np.exp(-t*400),0.5)
# riser (intro)
t = t_(1.1); f = 120+900*(t/1.1)**2; r = 0.5*np.sin(2*np.pi*np.cumsum(f)/SR) + bp_noise(len(t),(400,3000),(2000,10000))
S['riser'] = norm(r*(t/1.1)**2.2*np.minimum(1,(1.1-t)*60),0.75)
# shimmer (outro): major arpeggio
t = t_(2.2); sh = np.zeros(len(t))
for i,f in enumerate([523.25,659.25,783.99,1046.5,1318.5]):
    o = int(i*0.09*SR); tt = t[:len(t)-o]; sh[o:] += np.sin(2*np.pi*f*tt)*np.exp(-tt*2.2)*np.minimum(1,tt*300)
S['shimmer'] = norm(reverb(sh,0.6,0.35),0.6)
# money/counter end ding (higher)
t = t_(0.5); S['ding2'] = norm(sum(a*np.sin(2*np.pi*f*t)*np.exp(-t*k) for f,a,k in [(2093,1,8),(3136,.4,11)])*np.minimum(1,t*400),0.55)

if len(sys.argv) > 3:
    os.makedirs(sys.argv[3], exist_ok=True)
    for k,v in S.items(): sf.write(f"{sys.argv[3]}/{k}.wav", v.astype(np.float32), SR)

D = json.load(open(sys.argv[1])); dur = D['dur']
track = np.zeros((int((dur+3)*SR), 2))
last = {}
def place(name, t, g, pan=0.0, minsep=0.12):
    if t < 0 or (name in last and t-last[name] < minsep): return
    last[name] = t; x = S[name]*g; i = int(t*SR); e = min(len(track), i+len(x))
    l, r = np.sqrt(0.5*(1-pan)), np.sqrt(0.5*(1+pan))
    track[i:e,0] += x[:e-i]*l*1.41; track[i:e,1] += x[:e-i]*r*1.41
log = []
intro_icons = 0
for e in sorted(D['ev'], key=lambda e: e['v0']):
    v0 = e['v0']
    if e['wipe']: place('whoosh', v0+0.05, 0.55); log.append((v0,'whoosh'))
    elif e['a'] == 'slam':
        if v0 < 4 or v0 > dur-6:   # intro / outro logo bar
            place('riser', v0-1.0+0.15, 0.5); place('impact', v0+0.15, 0.75, minsep=1)
        else: place('impact', v0+0.12, 0.5, minsep=1)
        log.append((v0,'impact'))
    elif e['check']: place('ding', v0+0.12, 0.28, pan=0.2); log.append((v0,'ding'))
    elif e['count']:
        c = e['count']; t0 = c['t']+4.0; cd = c.get('dur',1.2)
        # ticks slowing down (easeOut)
        k = 0
        for s in np.linspace(0, 0.92, 16):
            tt = t0 + cd*(1-(1-s)**(1/3)); place('tick', tt, 0.22*(1-0.4*s), pan=0.3, minsep=0.03)
        place('ding2', t0+cd, 0.35, minsep=0.3); log.append((v0,'count'))
    elif e['a'] == 'pop' and e['box']: place('pop', v0+0.04, 0.42, pan=0.15); log.append((v0,'pop'))
    elif e['a'] == 'pop':
        if v0 < 4: place('softpop', v0+0.04, 0.3, minsep=0.08)
        else: place('softpop', v0+0.04, 0.25, pan=0.15)
        log.append((v0,'softpop'))
    elif e['photo']: place('swoosh', v0, 0.3, pan=-0.3, minsep=0.3); log.append((v0,'swoosh'))
    elif e['full'] and abs(v0-4.0) < 0.05: place('whoosh', v0-0.1, 0.55, minsep=1)
# outro shimmer (end card tiles)
place('shimmer', dur-4.5+0.75, 0.45)
place('whoosh', dur-4.5-0.25, 0.5, minsep=0.5)
track = track[:int(dur*SR)]
sf.write(sys.argv[2], track.astype(np.float32), SR)
from collections import Counter; print(Counter(n for _,n in log), 'peak', np.abs(track).max().round(2))
