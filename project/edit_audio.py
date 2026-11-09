import wave, json, numpy as np, noisereduce as nr, subprocess
SR=48000
w=wave.open('work/vo48k.wav'); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
# --- noise reduction: profile from quietest 2s of non-speech
H=SR//20; fr=a[:len(a)//H*H].reshape(-1,H); db=20*np.log10(np.sqrt((fr**2).mean(1))+1e-9)
quiet=np.where(db<np.percentile(db,8))[0]
noise=np.concatenate([a[i*H:(i+1)*H] for i in quiet])
a=nr.reduce_noise(y=a,sr=SR,y_noise=noise,stationary=True,prop_decrease=0.85,n_fft=2048)
# --- VAD on 10ms frames
H=SR//100; fr=a[:len(a)//H*H].reshape(-1,H); db=20*np.log10(np.sqrt((fr**2).mean(1))+1e-9)
sp=db>-42
# fill short holes (<250ms) and drop tiny blips (<60ms)
def runs(m):
    r=[];i=0
    while i<len(m):
        j=i
        while j<len(m) and m[j]==m[i]: j+=1
        r.append([m[i],i,j]); i=j
    return r
for v,i,j in runs(sp):
    if not v and j-i<25: sp[i:j]=True
for v,i,j in runs(sp):
    if v and j-i<6: sp[i:j]=False
manual_cut=[(205.15,205.95),(218.93,219.70),(242.55,244.50)]  # false starts / fillers / repeats
for t0,t1 in manual_cut: sp[int(t0*100):int(t1*100)]=False
segs=[(i/100,j/100) for v,i,j in runs(sp) if v]
scene_bounds=[10.2,40.6,81.3,118.3,152.0,186.0,227.1]
# --- build keep list: speech plus padding; gaps compressed
keep=[]; PAD=0.12
for k,(s,e) in enumerate(segs):
    s0=max(0,s-PAD); e0=min(len(a)/SR,e+PAD)
    if keep and s0<=keep[-1][1]: keep[-1][1]=e0
    else: keep.append([s0,e0])
# never let padding reach into a manual cut
nk=[]
for s0,e0 in keep:
    pieces=[[s0,e0]]
    for c0,c1 in manual_cut:
        np2=[]
        for a0,a1 in pieces:
            if c1<=a0 or c0>=a1: np2.append([a0,a1]); continue
            if a0<c0: np2.append([a0,c0])
            if c1<a1: np2.append([c1,a1])
        pieces=np2
    nk+= [p for p in pieces if p[1]-p[0]>0.05]
keep=nk
out=[]; mapping=[]; t_new=0.0; prev_end=None
LEAD=0.4
for k,(s,e) in enumerate(keep):
    if prev_end is not None:
        gap_orig=s-prev_end
        boundary=any(prev_end-0.5<=b<=s+0.5 for b in scene_bounds)
        g=min(gap_orig, 0.55 if boundary else 0.22)
        out.append(np.zeros(int(g*SR),np.float32)); t_new+=g
    else:
        out.append(np.zeros(int(LEAD*SR),np.float32)); t_new+=LEAD
    seg=a[int(s*SR):int(e*SR)].copy()
    f=int(0.015*SR); seg[:f]*=np.linspace(0,1,f); seg[-f:]*=np.linspace(1,0,f)
    mapping.append([s,e,t_new]); out.append(seg); t_new+=e-s; prev_end=e
out.append(np.zeros(int(1.0*SR),np.float32))
y=np.concatenate(out)
wv=wave.open('work/cut.wav','wb'); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
wv.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes()); wv.close()
json.dump({"map":mapping,"dur":len(y)/SR},open('work/map.json','w'))
print("orig",len(a)/SR,"new",len(y)/SR,"pieces",len(mapping))
