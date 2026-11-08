# Edit voice-over: remove retake, compress pauses, build new timeline + corrected words.
import json, numpy as np, soundfile as sf, re, sys
W="/tmp/claude-0/-home-user-video-claude-/2a734288-29af-5c47-8d50-5a13f3989741/scratchpad/work/"
a,sr=sf.read(W+"vo48_dn.wav")
tr=json.load(open(W+"tr_large.json"))
words=[dict(s=w["s"],e=w["e"],w=w["w"].strip()) for s in tr for w in s["words"]]
# --- fix words around 108.8-112 ("Sebanyak 1 bilion disediakan bagi")
fix=[]
for w in words:
    if 110.3<w["s"]<111.2 and w["w"] in ("ringgit.","Dan"):
        if w["w"]=="ringgit.": w=dict(s=110.46,e=111.18,w="disediakan")
        else: continue
    if abs(w["s"]-111.24)<0.01 and w["w"]=="bagi": w=dict(w,s=111.18)
    fix.append(w)
words=fix
# merge "1" ".5" and "50" "%"
m=[]
for w in words:
    if m and w["w"] in (".5","%") : m[-1]=dict(m[-1],e=w["e"],w=m[-1]["w"]+w["w"]); continue
    m.append(w)
words=m
REPL={"Perentukan":"Peruntukan","Melibuti":"Meliputi","AII":"AI","penyembunan":"penyempurnaan",
"e-invoice.":"e-Invois.","e-invoice":"e-Invois","penjajah":"penjaja,","keseruhan":"keseluruhan",
"peniagaan":"perniagaan","peniagaan.":"perniagaan.","peniagaan,":"perniagaan,","pickup":"pick-up","Budi95":"BUDI95",
"sekaligus":"sekali gus","madani":"MADANI","sejahtera":"Sejahtera","bilion.":"bilion","Budi":"BUDI","Madani,":"MADANI,","Madani":"MADANI","1.5":"1.5"}
for w in words:
    w["w"]=REPL.get(w["w"],w["w"])
    if w["w"]=="Disasarkan" and w["s"]>81: w["w"]="disasarkan"
# remove retake words (first take)
RETAKE=(78.94,80.97)
words=[w for w in words if not (RETAKE[0]-0.3<=w["s"]<RETAKE[1])]
# fix 'bilion' whisper periods: "1.5 bilion ringgit pada tahun 2027." - drop '5' leftover
words=[w for w in words if not (51.1<w["s"]<51.4 and ((w["w"]=="5") or (w["w"].startswith("bilion") and w["s"]<51.15)))]
m=[]
for w in words:
    if m and w["w"].startswith("-"): m[-1]=dict(m[-1],e=w["e"],w=m[-1]["w"]+w["w"]); continue
    m.append(w)
words=m
for w in words:
    if w["w"]in("e-invoice.","e-invoice"): w["w"]=w["w"].replace("e-invoice","e-Invois")
    if 109.5<w["s"]<110 and w["w"]=="1": w["w"]="RM1"
    if w["w"]=="50%": w["w"]="50%"
# --- panel starts (original time of first word) ---
PANELS=[("s1p1",2.30),("s1p2",6.36),("s1p3",14.0),("s1p4",21.18),
("s2p1",32.38),("s2p2",36.88),("s2p3",42.08),("s2p4",54.38),
("s3p1",65.50),("s3p2",73.82),("s3p3",86.56),("s3p4",94.56),
("s4p1",100.96),("s4p2",108.80),("s4p3",115.90),("s4p4",124.32),
("s5p1",130.62),("s5p2",135.14),("s5p3",145.26),("s5p4",148.98),
("s6p1",156.88),("s6p2",161.74),("s6p3",177.04),("s6p4",185.88)]
PANELS=[(k, [w for w in words if w["s"]>=ps-0.05][0]['s']) for k,ps in PANELS]
# --- energy VAD ---
hop=int(0.01*sr)
fr=np.array([np.sqrt(np.mean(a[i:i+hop]**2)) for i in range(0,len(a)-hop,hop)])
db=20*np.log10(fr+1e-9)
speech=db>-45
# smooth: fill tiny gaps < 60ms
idx=np.arange(len(speech))
# find pauses (non-speech runs >= 0.12s)
pauses=[]
i=0;n=len(speech)
while i<n:
    if not speech[i]:
        j=i
        while j<n and not speech[j]: j+=1
        if (j-i)*0.01>=0.12: pauses.append([i*0.01,j*0.01])
        i=j
    else: i+=1
# treat retake as removed region: merge into a pause spanning it
keep_cuts=[]  # list of (start,end) to remove
# leading / trailing
first=words[0]["s"]; last=words[-1]["e"]
def boundary_type(t):
    """classify pause at time t by neighbouring words"""
    prev=[w for w in words if w["e"]<=t+0.05]
    nxt=[w for w in words if w["s"]>=t-0.05]
    if not prev or not nxt: return "edge"
    pw=prev[-1]; nw=nxt[0]
    for k,ps in PANELS:
        if pw["e"]-0.05< ps <= nw["s"]+0.25 or abs(nw["s"]-ps)<0.2:
            return "section" if k.endswith("p1") else "panel"
    if pw["w"].endswith((".","?","!")): return "sentence"
    if pw["w"].endswith(","): return "comma"
    return "word"
TARGET={"edge":0.3,"section":0.95,"panel":0.45,"sentence":0.38,"comma":0.26,"word":0.16}
cuts=[]
# retake region: remove fully plus surrounding pause handled below
cuts.append(list(RETAKE))
for p0,p1 in pauses:
    if p1<=first-0.05 or p0>=last+0.05: continue
    if RETAKE[0]-0.05<=p0 and p1<=RETAKE[1]+0.05: continue
    # pause adjacent to retake: extend to include retake for classification
    bt=boundary_type((p0+p1)/2)
    tgt=TARGET[bt]
    L=p1-p0
    # keep a little extra from natural pause (breath feel) when it's not much longer
    if L>tgt+0.04:
        # remove middle, keep tail of previous word decay and pre-onset
        keep_pre=min(0.6*tgt, L/2); keep_post=tgt-keep_pre
        cuts.append([p0+keep_pre, p1-keep_post])
# merge retake with neighbouring pause: pause straddles 80.97..81.6 -> handled as generic pause
lead=max(0, first-0.35); tail=min(len(a)/sr, last+0.6)
cuts.append([0,lead]); cuts.append([tail,len(a)/sr])
cuts=sorted(cuts)
# merge overlaps
mc=[]
for c in cuts:
    if mc and c[0]<=mc[-1][1]: mc[-1][1]=max(mc[-1][1],c[1])
    else: mc.append(list(c))
cuts=mc
# section boundaries need >= target: if natural pause shorter, insert silence
# build keep list
keeps=[];t=0
for c0,c1 in cuts:
    if c0>t: keeps.append([t,c0])
    t=max(t,c1)
if t<len(a)/sr: keeps.append([t,len(a)/sr])
# insert silence at section/panel boundaries if natural gap shorter than target
inserts={}  # original time -> extra silence
for k,ps in PANELS[1:]:
    prev=[w for w in words if w["s"]<ps-0.01][-1]; nw=[w for w in words if w["s"]>=ps-0.01][0]
    gap_orig=nw["s"]-prev["e"]
    tgt=TARGET["section" if k.endswith("p1") else "panel"]
    if gap_orig<tgt-0.05:
        inserts[nw["s"]-0.03]=tgt-max(gap_orig,0)
# assemble audio with 8ms crossfades
XF=int(0.008*sr)
out=[];mapping=[]  # (orig_start, orig_end, new_start)
cur=0.0
pieces=[]
for k0,k1 in keeps:
    # split by inserts
    pts=[k0]+sorted([t for t in inserts if k0<t<k1])+[k1]
    for i in range(len(pts)-1):
        pieces.append((pts[i],pts[i+1]))
        if pts[i+1] in inserts: pieces.append(("sil",inserts[pts[i+1]]))
res=np.zeros(0)
for pc in pieces:
    if pc[0]=="sil":
        res=np.concatenate([res,np.zeros(int(pc[1]*sr))]); continue
    s0,s1=pc; seg=a[int(s0*sr):int(s1*sr)].copy()
    if len(seg)>2*XF:
        seg[:XF]*=np.linspace(0,1,XF); seg[-XF:]*=np.linspace(1,0,XF)
    mapping.append((s0,s1,len(res)/sr))
    res=np.concatenate([res,seg])
# prepend 0.6s intro silence
INTRO=0.6
res=np.concatenate([np.zeros(int(INTRO*sr)),res])
mapping=[(a0,a1,n0+INTRO) for a0,a1,n0 in mapping]
sf.write(W+"vo_edit.wav",res,sr)
def remap(t):
    best=None
    for a0,a1,n0 in mapping:
        if a0<=t<=a1: return n0+(t-a0)
        if t<a0: return n0  # in removed gap before this piece
    return mapping[-1][2]+(mapping[-1][1]-mapping[-1][0])
nw=[dict(w=w["w"],s=round(remap(w["s"]),3),e=round(remap(w["e"]),3)) for w in words]
pan=[dict(k=k,t=round(remap([w for w in words if w["s"]>=ps-0.01][0]["s"]),3)) for k,ps in PANELS]
json.dump(dict(words=nw,panels=pan,dur=len(res)/sr),open(W+"timeline.json","w"),ensure_ascii=False,indent=1)
print("orig",len(a)/sr,"new",len(res)/sr)
for p in pan: print(p)
print(" ".join(w["w"] for w in nw))
