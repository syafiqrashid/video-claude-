import json, sys
mp = json.load(open(sys.argv[2]))["segments"]
def f(t):
    for s in mp:
        a,b = s["src"]; c,d = s["dst"]
        if t < a: return c
        if t <= b: return c + (t-a)
    return mp[-1]["dst"][1]
tr = json.load(open(sys.argv[1]))
out=[]
for s in tr:
    out.append({"start":round(f(s["start"]),2),"end":round(f(s["end"]),2),"text":s["text"].strip(),
                "words":[{"s":round(f(w["s"]),2),"e":round(f(w["e"]),2),"w":w["w"].strip()} for w in s["words"]]})
json.dump(out, open(sys.argv[3],"w"), ensure_ascii=False, indent=1)
for s in out: print(f"[{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
