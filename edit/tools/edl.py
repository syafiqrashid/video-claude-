"""Edit decision list + caption builder. Source transcripts: whisper large-v3 (ms).
Writes tools/edl.json consumed by tools/build.py."""
import json, sys, re
W = sys.argv[1]  # dir with v1n.json / v2n.json

# (source, in, out, label) -- kept ranges in source seconds
SEGS = [
    ("v1",   7.25,  10.95, "hook-a"),
    ("v1",  11.65,  27.15, "berita-baik"),
    ("v1",  27.95,  37.25, "600-800"),
    ("v1",  38.70,  43.35, "panas"),
    ("v1",  45.20,  49.55, "aircon"),
    ("v1",  50.45,  55.55, "ruang-tambahan"),
    ("v1",  57.90,  77.85, "mangga+3caj"),     # jolok mangga 57.9-64.8 kept whole
    ("v1",  80.10,  94.75, "3caj"),
    ("v1",  97.95, 105.40, "sapu-1"),          # sapu sampah kept whole
    ("v1", 115.50, 119.10, "sapu-2"),
    ("v1", 125.00, 144.95, "sapu-3+pesan"),
    ("v1", 154.45, 155.45, "kesimpulannya"),
    ("v2",  13.00,  41.00, "kesimpulan-v2"),
]

def words(src):
    out=[]
    for s in json.load(open(f"{W}/{src}n.json")):
        for w in s["words"]:
            out.append([w["w"].strip(), w["s"], w["e"]])
    return out

# whisper drift fixes from re-transcribed slices (no-VAD)
OVR = {
 "v1": [((7,16), "Korang@7.6-8.04 bil@8.04-9.0 api@9.0-9.52 korang@9.52-9.82 naik@9.82-10.14 mendadak@10.14-10.5 bulan@10.5-10.68 ni,@10.68-10.84 jangan@11.72-12.4 stres.@12.4-13.0 Tunggu@13.08-13.5 dulu.@13.5-13.72 Ada@13.8-14.54 berita@14.54-14.88 baik@14.88-15.12 ni@15.12-15.3 untuk@15.3-15.46 korang.@15.46-15.8 Okey,@16.0-16.45"),
        ((64,69), "Apa@64.85-65.08 yang@65.08-65.44 korang@65.44-65.78 dapat@65.78-65.98 daripada@65.98-66.56 perlindungan@67.5-67.98 ni?@67.98-68.3 Kalau@68.67-69.05"),
        ((130.3,139), "Sekarang@131.36-131.76 saya@131.76-131.96 nak@131.96-132.1 pesan@132.1-132.34 kat@132.34-132.42 korang.@132.42-132.82 Tapi@132.82-133.32 ingat,@133.32-133.76 walaupun@133.86-134.62 had@134.62-134.8 perlindungan@134.8-135.38 dah@135.38-135.6 dinaikkan@135.6-136.36 kepada@136.36-136.74 800@136.74-137.1 kWh@137.1-137.7 sebulan,@137.7-138.6 tapi@138.92-139.46"),
        ((141.7,146), "Jimat@141.76-142.6 elektrik,@142.6-143.38 jimat@143.38-144.08 juga@144.08-144.2 duit@144.2-144.52 kita.@144.52-144.84"),
        ((154,156), "Kesimpulannya...@154.56-155.4")],
}
FIX = {"Ahmadiyah":"MADANI","800kW":"800","kW":"kWh","otomatik":"automatik","si":"isi","di":"","lindungi":"dilindungi",
       "Madani":"MADANI","madani":"MADANI","Okey,":"Okey,","-kawan":None}
def fixed(src):
    ws = words(src)
    for (a,b),txt in OVR.get(src,[]):
        ws=[w for w in ws if not (a<=w[1]<b)]
        for t in txt.split():
            m=re.match(r"(.+)@([\d.]+)-([\d.]+)",t); ws.append([m[1],float(m[2]),float(m[3])])
    ws.sort(key=lambda w:w[1])
    out=[]
    for w in ws:
        t=w[0]
        if t=="-kawan" and out: out[-1][0]+="-kawan"; out[-1][2]=w[2]; continue
        if t in FIX: t=FIX[t]
        if t=="jam" and out and out[-1][0] in("800","kWh"): out[-1][0]= "800" if out[-1][0]=="800" else out[-1][0]; t="kWh"
        if not t: continue
        out.append([t,w[1],w[2]])
    # merge "800 kWh" if whisper split oddly
    return out

edl=[]; caps=[]; t=0.0
WS={s:fixed(s) for s in ("v1","v2")}
for i,(src,a,b,label) in enumerate(SEGS):
    edl.append(dict(id=f"c{i}",src=src,mi=a,mo=b,start=round(t,3),dur=round(b-a,3),label=label))
    for w,s,e in WS[src]:
        if s>=a-0.8 and s<b-0.05 and e>a+0.1:
            caps.append([w, round(t+max(s,a)-a,3), round(t+min(e,b)-a,3)])
    t+=b-a
# drop duplicate kWh tokens ("kWh kWh")
clean=[]
for c in caps:
    if clean and c[0]=="kWh" and clean[-1][0]=="kWh": continue
    clean.append(c)
json.dump(dict(total=round(t,3),edl=edl,words=clean),open("tools/edl.json","w"),ensure_ascii=False,indent=1)
print("TOTAL",round(t,2))
for e in edl: print(f'{e["id"]:4} {e["src"]} {e["mi"]:7.2f}-{e["mo"]:7.2f} -> out {e["start"]:7.2f} (+{e["dur"]:.2f}) {e["label"]}')
print(" ".join(f"{w}@{s:.1f}" for w,s,e in clean))
