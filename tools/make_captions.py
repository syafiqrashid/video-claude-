# Split corrected script into caption chunks timed from word-level transcript of final audio
import json, re, sys
src = open(sys.argv[1]).read()
items = [(float(t), txt) for t, txt in re.findall(r't:\s*([\d.]+),\s*txt:\s*"([^"]+)"', src)]
end = float(re.search(r'AUDIO_END\s*=\s*([\d.]+)', src)[1])
words = [w for s in json.load(open(sys.argv[2])) for w in s["words"]]
caps = []
for i, (t0, txt) in enumerate(items):
    t1 = items[i+1][0] if i+1 < len(items) else end
    ws = [w for w in words if t0-0.15 <= w["s"] < t1-0.05]
    st = ws[0]["s"] if ws else t0; en = ws[-1]["e"] if ws else t1
    toks = txt.split()
    # chunk: max 8 words, prefer break after comma
    chunks, cur = [], []
    for tk in toks:
        cur.append(tk)
        if len(cur) >= 8 or (tk.endswith(',') and len(cur) >= 4):
            chunks.append(cur); cur = []
    if cur:
        if chunks and len(cur) <= 2: chunks[-1] += cur
        else: chunks.append(cur)
    n = len(toks); k = 0
    for j, ch in enumerate(chunks):
        a = k / n; k += len(ch); b = k / n
        # map word fraction to recognised-word timings
        def at(f):
            if not ws: return t0 + f*(t1-t0)
            idx = min(len(ws)-1, int(round(f*(len(ws)))))
            return ws[idx]["s"] if f < 1 else en
        cs, ce = (st if j == 0 else at(a)), (en + 0.25 if j == len(chunks)-1 else at(b))
        html = " ".join(ch)
        html = re.sub(r'(RM[\d.]+(?: (?:bilion|juta))?|\b\d[\d.,%]*(?: (?:liter|juta|ribu|bulan|tahun))?|BUDI95|BUDI Diesel|BUDI MADANI|Geran Sejahtera MADANI)', r'<em>\1</em>', html)
        caps.append({"t": round(cs, 2), "e": round(ce, 2), "html": html})
for a, b in zip(caps, caps[1:]):
    if a["e"] > b["t"]: a["e"] = b["t"]
open(sys.argv[3], "w").write("window.CAPS = " + json.dumps(caps, ensure_ascii=False, indent=0) + ";\n")
print(len(caps), "captions"); [print(c) for c in caps[:6]]
