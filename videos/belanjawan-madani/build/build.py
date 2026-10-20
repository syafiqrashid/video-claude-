"""Generate index.html from the edit decision list (edl.json) and Whisper word timings.

Run:  python3 -I build/build.py   (from the project root)

Source times in this file are seconds in the ORIGINAL clip (A = main take, B = outro).
They are mapped to timeline time through the EDL, so re-cutting only needs edl.json edits.
"""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
EDL = json.load(open(os.path.join(B, "edl.json")))
WORDS = {k: json.load(open(os.path.join(B, f"{k}.json"))) for k in "AB"}
for c in EDL:  # "dur" is timeline seconds; a clip with "rate" consumes dur * rate of source
    c.setdefault("rate", 1)
    c["src_end"] = round(c["media_start"] + c["dur"] * c["rate"], 3)
TOTAL = round(sum(c["dur"] for c in EDL), 2)
W, H = 1080, 1920


def tl_time(src, t):
    """Map a source time to timeline time; None if the moment was cut."""
    for c in EDL:
        if c["src"] == src and c["media_start"] <= t < c["src_end"]:
            return round(c["start"] + (t - c["media_start"]) / c["rate"], 3)
    return None


def clip_of(src, t):
    for c in EDL:
        if c["src"] == src and c["media_start"] <= t < c["src_end"]:
            return c
    return None


def clip_at(src, t):
    for c in EDL:
        if c["src"] == src and c["media_start"] - 0.5 <= t < c["src_end"]:
            return c
    return None


# ---------------------------------------------------------------- transcript fixes
FIX = {
    "belanjauan": "Belanjawan", "Malay": "Madani", "hara": "sara", "sehat,": "sihat,",
    "diperentukkan": "diperuntukkan", "tekanan": "tingkatan", "Perutukan": "Peruntukan",
    "pemelanjakan": "perbelanjaan", "pengajar": "pengajian", "merengankan": "meringankan",
    "perentukan": "peruntukan", "ditingkat": "ditingkatkan", "kandil": "",
    "batuan": "Bantuan", "sarah": "SARA", "madani": "Madani", "tetap": "tertakluk", "luk": "",
    "sterma": "terma", "mengatahui": "mengetahui", "Rahma": "Rahmah", "perdukan": "peruntukan",
    "Madami": "MADANI", "150": "RM150", "2": "dua", "-6,": "-6,",
}
ACCENT = re.compile(r"^(RM[\d,]+|[\d,]+%?|\d+|juta|bilion|ribu|STR|SARA|RMT|MADANI|Madani|2027|enam|dua|ke-6,?)[,.?!]*$", re.I)


def words_for(src):
    out = []
    for seg in WORDS[src]:
        for wi, w in enumerate(seg["words"]):
            txt = w["w"].strip()
            if txt in FIX:
                txt = FIX[txt]
            # glue whisper sub-tokens (",500", "%", "-anak") onto the previous word
            if out and txt and (txt[0] in ",%-" or txt.startswith(",")) and w["s"] - out[-1]["e"] < 0.3:
                out[-1]["t"] += txt
                out[-1]["e"] = w["e"]
                continue
            if txt in ("2",) and src == "A" and w["s"] > 160:
                txt = "RM2"
            out.append({"t": txt, "s": w["s"], "e": w["e"], "first": wi == 0})
    for o in out:
        o["t"] = o["t"].replace("RM2,500", "RM2,500").replace("90,000", "90,000")
        if o["t"] in ("RM90,000",):
            o["t"] = "90,000"
    return [o for o in out if o["t"]]


def caption_groups():
    groups = []
    for src in "AB":
        cur = []
        for w in words_for(src):
            ts, te = tl_time(src, w["s"] + 0.02), tl_time(src, max(w["s"] + 0.02, w["e"] - 0.02))
            if ts is None and te is not None:
                ts = max(te - 0.25, clip_of(src, w["e"] - 0.02)["start"])
            if ts is None:
                if cur:
                    groups.append(cur); cur = []
                continue
            if te is None or te < ts:
                te = ts + 0.25
            word = {"t": w["t"], "s": ts, "e": te}
            word["clip"] = clip_of(src, w["e"] - 0.02) or clip_of(src, w["s"] + 0.02)
            if cur and (len(cur) >= 3 or ts - cur[-1]["e"] > 0.35 or re.search(r"[,.?!]$", cur[-1]["t"])
                        or w["first"] or word["clip"] is not cur[-1]["clip"]):
                groups.append(cur); cur = []
            word["src_s"] = w["s"]
            cur.append(word)
        if cur:
            groups.append(cur)
    groups.sort(key=lambda g: g[0]["s"])
    merged = []
    for g in groups:  # fold a lone orphan word back into the phrase it belongs to
        p = merged[-1] if merged else None
        if (p and len(g) == 1 and len(p) <= 3 and g[0]["clip"] is p[-1]["clip"]
                and g[0]["s"] - p[-1]["e"] < 0.4 and not re.search(r"[,.?!]$", p[-1]["t"])):
            p.extend(g)
        else:
            merged.append(g)
    groups = merged
    res = []
    for g in groups:
        s = g[0]["s"]
        e = g[-1]["e"] + 0.18
        res.append({"s": round(s, 3), "e": round(e, 3), "w": [{"t": x["t"], "s": round(x["s"], 3)} for x in g]})
    # no overlap: each group ends when the next starts
    for a, b in zip(res, res[1:]):
        if a["e"] > b["s"] - 0.02:
            a["e"] = round(b["s"] - 0.02, 3)
    return res


# ---------------------------------------------------------------- graphics plan (source times)
SECTIONS = [  # (n, title, sub, src, start_src, end_src)
    (1, "Bantuan Awal Persekolahan", "BAP", "A", 21.95, 33.3),
    (2, "Rancangan Makanan Tambahan", "RMT", "A", 40.5, 60.6),
    (3, "Pelajar Tingkatan 6", "Bantuan pengajian", "A", 155.55, 174.6),
    (4, "STR & SARA", "Bantuan tunai rakyat", "A", 182.35, 205.2),
    (5, "SARA Madani", "Bantuan one-off", "A", 229.7, 253.2),
    (6, "Jualan Rahmah & Agro Madani", "Barangan dapur", "A", 255.4, 282.3),
]
# big number callouts: (src, t_in, t_out, kicker, big, foot, sfx)
CALLOUTS = [
    ("A", 29.15, 33.3, "BAP SETIAP MURID", "RM200", "dahulu RM150", "ping"),
    ("A", 45.3, 50.4, "PERUNTUKAN RMT", "RM870 JUTA", "makanan tambahan di sekolah", "ping"),
    ("A", 54.3, 58.2, "MANFAAT KEPADA", "800 RIBU+", "murid yang layak", "pop"),
    ("A", 162.6, 167.2, "SETIAP PELAJAR", "RM2,500", "tingkatan 6", "ping"),
    ("A", 164.4, 171.3, "MANFAAT KEPADA", "90,000", "murid", "pop"),
    ("A", 189.4, 192.4, "STR + SARA 2027", "RM16 BILION", "ditingkatkan", "impact-bass-1"),
    ("A", 195.0, 201.3, "SARA SEHINGGA", "RM150", "sebulan · barangan asas", "ping"),
    ("A", 234.9, 238.2, "SARA MADANI", "RM100 × 2", "dua kali bayaran", "ping"),
    ("A", 238.2, 245.3, "LAYAK", "18 TAHUN+", "bukan penerima STR · tertakluk syarat", "pop"),
    ("A", 263.9, 266.9, "PERUNTUKAN", "RM750 JUTA", "Jualan Rahmah & Agro Madani", "ping"),
    ("A", 273.9, 279.0, "HARGA LEBIH MURAH", "30%", "melalui Jualan Agro Madani", "impact-bass-1"),
]
CHIPS = [("A", 267.3, "Ayam"), ("A", 268.1, "Ikan"), ("A", 268.6, "Sayur"), ("A", 269.7, "Buah")]
# casual (santai) beats kept on purpose: playful sticker over each one
STICKERS = [("A", 33.6, 40.2, "Semak fakta jap…"), ("A", 61.0, 69.5, "Rehat jap, minum dulu"),
            ("A", 175.0, 182.0, "Cek penampilan dulu!"), ("A", 147.8, 155.3, "Air dulu, baru sambung!"),
            ("A", 253.9, 255.5, "Bos kecil dah sampai!"), ("A", 224.6, 229.6, "Catat nota jap…")]
HOOK_FLASH = ["RM200", "RM870 JUTA", "RM16 BILION", "30% MURAH"]
RECAP = ["Bantuan Awal Persekolahan RM200", "RMT RM870 juta", "Tingkatan 6 RM2,500",
         "STR & SARA RM16 bilion", "SARA Madani RM100 × 2", "Jualan Rahmah & Agro Madani"]


def T(src, t):
    v = tl_time(src, t)
    if v is None:
        c = clip_at(src, t)
        v = c["start"] if c else None
    assert v is not None, (src, t)
    return v


def build():
    caps = caption_groups()
    sfx = []  # (name, t, vol)

    def add_sfx(name, t, vol=0.35):
        sfx.append((name, round(max(0, t), 3), vol))

    # ---- video clips (each EDL row is one clip of the same source)
    vids, zooms = [], []
    prev_src_end = None
    z = 1.0
    for i, c in enumerate(EDL):
        # alternate a punch-in whenever two pieces of the same take are butted together (hides the jump cut)
        gap = None if prev_src_end is None else abs(c["media_start"] - prev_src_end)
        if gap is not None and gap < 0.05:
            pass  # seamless continuation of the same take: keep the framing
        elif gap is not None and gap < 2.0:
            z = 1.14 if z == 1.0 else 1.0
        else:
            z = 1.0
        prev_src_end = c["src_end"]
        if c["id"] == "salam":
            z = 1.14
        zooms.append(z)
        rate = f'data-playback-rate="{c["rate"]}" data-volume="0.7" ' if c["rate"] != 1 else ""
        vids.append(
            f'<video id="v{i:02d}" class="clip vid" src="assets/{c["src"]}.mp4" data-start="{c["start"]}" '
            f'data-duration="{c["dur"]}" data-media-start="{c["media_start"]}" data-track-index="0" {rate}'
            f'playsinline data-has-audio="true" style="transform: scale({z}); z-index: 1"></video>'
        )

    # ---- section badges + wipes + progress
    sections = []
    for n, title, sub, src, a, b in SECTIONS:
        s, e = T(src, a), T(src, b - 0.05)
        sections.append({"n": n, "title": title, "sub": sub, "s": s, "e": e})
        add_sfx("whoosh", s - 0.12, 0.4)
    callouts = []
    for src, a, b, kick, big, foot, snd in CALLOUTS:
        s, e = T(src, a), T(src, b - 0.05)
        callouts.append({"s": s, "e": e, "k": kick, "b": big, "f": foot})
        add_sfx(snd, s, 0.3 if snd != "impact-bass-1" else 0.45)
    chips = [{"s": T(src, t), "t": txt} for src, t, txt in CHIPS]
    for c in chips:
        add_sfx("pop", c["s"], 0.28)

    stickers = [{"s": T(src, a), "e": T(src, b), "t": txt} for src, a, b, txt in STICKERS]
    for st in stickers:
        add_sfx("pop", st["s"], 0.35)

    hook_end = EDL[0]["dur"]
    hook_flash = [{"s": round(0.55 + i * 0.95, 3), "t": t} for i, t in enumerate(HOOK_FLASH)]
    for h in hook_flash:
        add_sfx("click-soft", h["s"], 0.45)
    hook_title_s = 4.6
    add_sfx("impact-bass-1", hook_title_s, 0.5)
    add_sfx("whoosh", hook_end - 0.15, 0.35)

    six_s = T("A", 16.40)
    add_sfx("impact-bass-1", six_s, 0.35)

    outro_start = next(c["start"] for c in EDL if c["src"] == "B")
    recap = [{"s": round(outro_start + 0.35 + i * 0.55, 3), "t": t} for i, t in enumerate(RECAP)]
    add_sfx("whoosh", outro_start - 0.1, 0.35)
    for r in recap:
        add_sfx("click-soft", r["s"], 0.4)
    recap_end = T("B", 5.30)
    quote_s, quote2_s = T("B", 20.0), T("B", 22.5)
    cta_s = T("B", 27.44)
    add_sfx("sparkle", quote_s, 0.3)
    add_sfx("chime", cta_s, 0.35)

    data = {
        "total": TOTAL, "caps": caps, "sections": sections, "callouts": callouts, "chips": chips, "stickers": stickers,
        "hookEnd": hook_end, "hookFlash": hook_flash, "hookTitle": hook_title_s, "six": six_s,
        "recap": recap, "recapEnd": recap_end, "quote": quote_s, "quote2": quote2_s, "cta": cta_s,
        "punches": [c["s"] for c in callouts],
    }

    sfx.sort(key=lambda x: x[1])
    durs = {"whoosh": 0.6, "whoosh-short": 0.4, "pop": 0.72, "ping": 1.32, "impact-bass-1": 2.12,
            "chime": 2.5, "click-soft": 0.37, "sparkle": 1.8}
    sfx_html = "\n".join(
        f'      <audio id="sfx-{i:02d}-{n}" class="clip" src="assets/sfx/{n}.mp3" data-start="{t}" '
        f'data-duration="{min(durs[n], TOTAL - t):.2f}" data-track-index="{20 + i % 4}" data-volume="{v}"></audio>'
        for i, (n, t, v) in enumerate(sfx) if t < TOTAL - 0.1
    )

    tpl = open(os.path.join(B, "template.html")).read()
    out = (tpl.replace("{{TOTAL}}", str(TOTAL))
              .replace("{{VIDEOS}}", "\n      ".join(vids))
              .replace("{{SFX}}", sfx_html)
              .replace("{{DATA}}", json.dumps(data, ensure_ascii=False)))
    open(os.path.join(ROOT, "index.html"), "w").write(out)
    print("index.html written · duration", TOTAL, "s ·", len(EDL), "clips ·", len(caps), "caption groups ·", len(sfx), "sfx")


if __name__ == "__main__":
    build()
