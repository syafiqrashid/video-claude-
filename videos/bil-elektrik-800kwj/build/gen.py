#!/usr/bin/env python3
"""Generates index.html: cut list + captions + motion graphics + SFX.

Every overlay is keyed to SOURCE time (seconds in assets/source.mp4) and mapped
to output time through the cut list, so re-trimming a piece moves everything.
"""
import json, html, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1080, 1920

# ---------------------------------------------------------------- cut list
# (src_in, src_out, zoom) — retakes, false starts, b-roll and dead air removed.
PIECES = [
    (8.50, 11.00, 1.00),   # Bila bil korang naik mendadak bulan ini
    (11.85, 14.00, 1.14),  # jangan stres, tunggu dulu
    (14.35, 15.80, 1.00),  # Ada berita baik ni untuk korang
    (16.30, 17.85, 1.10),  # Kerajaan MADANI ni
    (18.50, 20.45, 1.00),  # sekarang dah menjalankan langkah segera
    (20.90, 27.10, 1.10),  # daripada September 2026 sehingga 31 Disember 2026
    (27.80, 37.20, 1.00),  # Perlindungan ... 600 -> 800 kWj sebulan. Ok kenapa?
    (37.95, 39.85, 1.14),  # Sekarang korang boleh rasa kan
    (40.15, 43.55, 1.00),  # cuaca panas kering dengan jerebunya lagi
    (45.10, 49.45, 1.12),  # kipas dengan aircond ... betul kan?
    (50.25, 55.75, 1.00),  # Sebab tu kerajaan beri ruang tambahan 800 kWj
    (65.00, 95.10, 1.06),  # Apa yang korang dapat ... 3 caj ... dilindungi
    (133.15, 133.80, 1.14),  # Tapi ingat
    (134.15, 142.00, 1.00),  # walaupun had ... berhemah ya
    (142.65, 145.30, 1.14),  # jimat elektrik, jimat juga duit kita
    (199.45, 228.00, 1.04),  # Kesimpulannya ... Terima kasih (2nd, cleaner take)
]
starts = []
t = 0.0
for a, b, _ in PIECES:
    starts.append(round(t, 3))
    t = round(t + b - a, 3)
TOTAL = round(t, 3)


def o(src):
    """Map a source time to output time (snaps to the next piece if cut)."""
    for (a, b, _), s in zip(PIECES, starts):
        if src < a:
            return s
        if src <= b:
            return round(s + src - a, 3)
    return TOTAL


# ---------------------------------------------------------------- captions
FIX = {  # word start (src) -> corrected text ; None drops the word
    9.02: "bil", 10.14: "mendadak", 16.94: "MADANI", 25.18: "Disember",
    38.78: "korang", 38.94: None, 41.70: "gila", 46.10: "aircond", 46.30: None,
    46.40: "korang", 46.60: None, 77.48: "ialah", 79.76: "caj", 82.54: "pelarasan",
    87.16: "caj", 90.28: "caj", 75.88: "caj", 91.14: "SST.", 93.86: "isi", 94.24: "dilindungi", 94.36: None,
    134.66: "had", 218.38: "dilindungi", 218.60: None, 221.90: "MADANI",
    225.94: "kawan-kawan", 226.08: None, 199.96: "Kesimpulannya,",
}
words = []
for seg in json.load(open(os.path.join(HERE, "transcript.json"))):
    for w in seg["words"]:
        s, e, txt = round(w["s"], 2), round(w["e"], 2), w["w"].strip()
        if s in FIX:
            if FIX[s] is None:
                continue
            txt = FIX[s]
        txt = txt.replace("kWh", " kWj").replace("..", "").replace("...", "")
        if not any(a - 0.05 <= s and s < b for a, b, _ in PIECES):
            continue
        words.append([o(s), txt])

HOOK_END = o(15.80)
chunks, cur = [], []
for i, (ts, txt) in enumerate(words):
    if ts < HOOK_END:
        continue  # hook is carried by the kinetic title
    cur.append([ts, txt])
    nxt = words[i + 1][0] if i + 1 < len(words) else None
    end_punct = txt[-1] in ".,?!"
    if len(cur) >= 3 or end_punct or nxt is None or nxt - ts > 0.9:
        chunks.append(cur)
        cur = []
cap_html, cap_js = [], []
for ci, ch in enumerate(chunks):
    st = ch[0][0] - 0.04
    nxt_start = chunks[ci + 1][0][0] - 0.04 if ci + 1 < len(chunks) else TOTAL
    en = min(nxt_start, ch[-1][0] + 1.4)
    spans = "".join(
        f'<span class="w" id="c{ci}w{j}">{html.escape(t.rstrip(",.").upper())}</span> '
        for j, (_, t) in enumerate(ch)
    )
    cap_html.append(
        f'<div class="cap clip" id="cap{ci}" data-start="{st:.3f}" data-duration="{en - st:.3f}" data-track-index="5"><div class="capin" id="capin{ci}">{spans.strip()}</div></div>'
    )
    cap_js.append(f'tl.fromTo("#capin{ci}",{{y:18,opacity:0}},{{y:0,opacity:1,duration:0.16,ease:"power2.out"}},{st:.3f});')
    for j, (ts, _) in enumerate(ch):
        cap_js.append(f'tl.fromTo("#c{ci}w{j}",{{color:"#FFF8E7",scale:1}},{{color:"#FFD23F",scale:1.08,duration:0.08}},{ts:.3f});')
        if j + 1 < len(ch):
            cap_js.append(f'tl.to("#c{ci}w{j}",{{color:"#FFF8E7",scale:1,duration:0.08}},{ch[j+1][0]:.3f});')

# ---------------------------------------------------------------- SFX
SFX_LEN = {"whoosh": 0.57, "whoosh-short": 0.57, "impact-bass-1": 2.1, "impact-bass-2": 2.59,
           "pop": 0.72, "chime": 2.5, "sparkle": 1.8, "ping": 1.32, "click": 0.36,
           "notification": 2.45, "riser": 10.0}
SFX_PEAK = {"whoosh": 0.16, "whoosh-short": 0.16, "impact-bass-1": 0.07, "impact-bass-2": 1.99,
            "pop": 0.12, "chime": 0.02, "sparkle": 0.05, "ping": 0.32, "click": 0.02,
            "notification": 0.05, "riser": 0}
sfx = []


def S(name, at, vol=0.5, dur=None):
    """Place an SFX so its peak lands on output time `at`."""
    st = max(0.0, at - SFX_PEAK[name])
    sfx.append((name, round(st, 3), dur or SFX_LEN[name], vol))


# ---------------------------------------------------------------- overlays
ov_html, ov_js = [], []


def clip(id_, st, en, inner, cls="ov"):
    ov_html.append(f'<div class="{cls} clip" id="{id_}" data-start="{st:.3f}" data-duration="{en - st:.3f}" data-track-index="3">{inner}</div>')


ICON = {
    "bolt": '<svg viewBox="0 0 24 24"><path d="M13 2 4 14h6l-1 8 9-12h-6z" fill="#FFD23F" stroke="#0E1B3D" stroke-width="1.2" stroke-linejoin="round"/></svg>',
    "sun": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.5" fill="#FFB020"/><g stroke="#FFB020" stroke-width="2" stroke-linecap="round"><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></g></svg>',
    "haze": '<svg viewBox="0 0 24 24"><g stroke="#B9C2D6" stroke-width="2.2" stroke-linecap="round" fill="none"><path d="M3 8h13a3 3 0 1 0-3-3"/><path d="M3 13h17"/><path d="M3 18h10a3 3 0 1 1-3 3"/></g></svg>',
    "fan": '<svg viewBox="0 0 24 24"><g fill="#7FD1FF"><path d="M12 11c-1-4 0-8 3-8s3 4-3 8z"/><path d="M13 12c4-1 8 0 8 3s-4 3-8-3z"/><path d="M12 13c1 4 0 8-3 8s-3-4 3-8z"/><path d="M11 12c-4 1-8 0-8-3s4-3 8 3z"/></g><circle cx="12" cy="12" r="1.6" fill="#0E1B3D"/></svg>',
    "ac": '<svg viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="8" rx="2" fill="#E8EEF9"/><path d="M5 10h14" stroke="#0E1B3D" stroke-width="1.2"/><g stroke="#7FD1FF" stroke-width="1.8" stroke-linecap="round"><path d="M7 16v3M12 16v4M17 16v3"/></g></svg>',
    "check": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#3DDC84"/><path d="M6.5 12.5l3.5 3.5 7.5-8" stroke="#0E1B3D" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "warn": '<svg viewBox="0 0 24 24"><path d="M12 2 1 21h22z" fill="#FFD23F" stroke="#0E1B3D" stroke-width="1" stroke-linejoin="round"/><path d="M12 9v5" stroke="#0E1B3D" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="17.4" r="1.4" fill="#0E1B3D"/></svg>',
    "house": '<svg viewBox="0 0 24 24"><path d="M3 11 12 3l9 8v10H3z" fill="#FFF8E7"/><path d="M9.5 21v-6h5v6" fill="#0E1B3D"/><path d="M12 6.5 9.8 11h2.4L11 15l3.3-5h-2.5z" fill="#FFD23F"/></svg>',
    "cal": '<svg viewBox="0 0 24 24"><rect x="2.5" y="4" width="19" height="17" rx="2.5" fill="#FFF8E7"/><rect x="2.5" y="4" width="19" height="5" rx="2" fill="#FF5A4E"/><g stroke="#0E1B3D" stroke-width="2" stroke-linecap="round"><path d="M7 2.5v3M17 2.5v3"/></g><g fill="#0E1B3D"><circle cx="8" cy="13" r="1.2"/><circle cx="12" cy="13" r="1.2"/><circle cx="16" cy="13" r="1.2"/><circle cx="8" cy="17" r="1.2"/><circle cx="12" cy="17" r="1.2"/></g></svg>',
    "coin": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#FFD23F" stroke="#B88A00" stroke-width="1.5"/><text x="12" y="16" text-anchor="middle" font-family="Archivo Black" font-size="9" fill="#7A5A00">RM</text></svg>',
    "share": '<svg viewBox="0 0 24 24"><g fill="#0E1B3D"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/></g><path d="M8.6 10.5l6.8-4M8.6 13.5l6.8 4" stroke="#0E1B3D" stroke-width="2"/></svg>',
    "scale": '<svg viewBox="0 0 24 24"><g stroke="#FFD23F" stroke-width="1.8" fill="none" stroke-linecap="round"><path d="M12 3v18M6 21h12M4 7h16"/><path d="M4 7l-2.5 6h5zM20 7l-2.5 6h5z" fill="#FFD23F"/></g></svg>',
}


def ic(name, cls="ico"):
    return f'<span class="{cls}">{ICON[name]}</span>'


# 1 — HOOK (kinetic title replaces captions)
h0, h1, h2, h3 = o(8.50), o(11.85), o(14.35), o(15.80)
clip("hook", h0, h3 + 0.25,
     f'<div class="hook-band" id="hookA">{ic("bolt","bolt")}<div class="hk-sm">BIL ELEKTRIK</div><div class="hk-xl">NAIK<br>MENDADAK?</div></div>'
     f'<div class="hook-band" id="hookB"><div class="hk-xl">JANGAN<br>STRES!</div><div class="hk-sm">tunggu dulu…</div></div>'
     f'<div class="hook-band" id="hookC"><div class="hk-sm">ADA</div><div class="hk-xl yl">BERITA<br>BAIK!</div></div>')
ov_js += [
    f'tl.fromTo("#hookA .hk-sm",{{y:-60,opacity:0}},{{y:0,opacity:1,duration:0.3,ease:"back.out(2)"}},{h0+0.05});',
    f'tl.fromTo("#hookA .hk-xl",{{scale:2.4,opacity:0}},{{scale:1,opacity:1,duration:0.28,ease:"power4.in"}},{o(9.6)-0.28});',
    f'tl.fromTo("#hookA .bolt",{{scale:0,rotation:-40}},{{scale:1,rotation:0,duration:0.4,ease:"back.out(3)"}},{o(9.6)});',
    f'tl.to("#hookA .bolt",{{rotation:8,duration:0.12,yoyo:true,repeat:5}},{o(9.6)+0.4});',
    f'tl.to("#hookA",{{x:-1100,duration:0.25,ease:"power3.in"}},{h1-0.12});',
    f'tl.fromTo("#hookB",{{x:1100}},{{x:0,duration:0.3,ease:"power3.out"}},{h1+0.05});',
    f'tl.fromTo("#hookB .hk-sm",{{opacity:0}},{{opacity:1,duration:0.2}},{o(13.30)});',
    f'tl.to("#hookB",{{scale:0.6,opacity:0,duration:0.2,ease:"power2.in"}},{h2-0.1});',
    f'tl.fromTo("#hookC",{{scale:0.4,opacity:0}},{{scale:1,opacity:1,duration:0.45,ease:"elastic.out(1,0.55)"}},{o(14.62)});',
    f'tl.to("#hookC",{{opacity:0,y:-80,duration:0.25}},{h3});',
]
S("impact-bass-1", o(9.6), 0.30)
S("whoosh", h1 + 0.15, 0.55)
S("sparkle", o(14.62), 0.45)
S("pop", o(14.62), 0.5)

# 2 — top tag: Kerajaan MADANI, langkah segera
tA, tB = o(16.30), o(20.45)
clip("tag1", tA, tB, '<div class="tag" id="tag1in"><span class="dot"></span>KERAJAAN MADANI · LANGKAH SEGERA</div>', "ov top")
ov_js += [f'tl.fromTo("#tag1in",{{y:-140}},{{y:0,duration:0.4,ease:"back.out(1.6)"}},{tA});',
          f'tl.to("#tag1in",{{y:-160,duration:0.25,ease:"power2.in"}},{tB-0.25});']
S("whoosh-short", tA + 0.1, 0.4)

# 3 — date range card
d0, d1 = o(21.94), o(27.10)
clip("date", d0 - 0.1, d1,
     f'<div class="card" id="datecard">{ic("cal","ico big")}<div><div class="lbl">TEMPOH PERLINDUNGAN</div>'
     f'<div class="dt"><span id="dtA">SEPT 2026</span><span class="arr">→</span><span id="dtB">31 DIS 2026</span></div></div></div>', "ov mid")
ov_js += [f'tl.fromTo("#datecard",{{scale:0.7,opacity:0}},{{scale:1,opacity:1,duration:0.35,ease:"back.out(2)"}},{d0-0.1});',
          f'tl.fromTo("#dtA",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.25}},{d0});',
          f'tl.fromTo("#datecard .arr",{{opacity:0,scale:0}},{{opacity:1,scale:1,duration:0.2}},{o(23.70)});',
          f'tl.fromTo("#dtB",{{opacity:0,x:30}},{{opacity:1,x:0,duration:0.25}},{o(24.62)});',
          f'tl.to("#datecard",{{scale:0.8,opacity:0,duration:0.2}},{d1-0.2});']
S("pop", d0, 0.45)
S("click", o(24.62), 0.5)

# 4 — the headline number: 600 -> 800 kWj
n0, n6, n8, n1 = o(27.90), o(31.74), o(33.72), o(36.10)
clip("num", n0, n1,
     '<div class="card numcard" id="numcard"><div class="lbl">PERLINDUNGAN BIL ELEKTRIK DOMESTIK</div>'
     '<div class="nums"><div class="old" id="n600">600<s id="strike"></s></div><div class="arr2" id="narr">→</div><div class="new" id="n800">800</div></div>'
     '<div class="unit">kWj / sebulan</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#numcard",{{y:120,opacity:0}},{{y:0,opacity:1,duration:0.4,ease:"power3.out"}},{n0});',
          f'tl.fromTo("#n600",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2.5)"}},{n6-0.05});',
          f'tl.fromTo("#narr",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.25}},{o(33.10)});',
          f'tl.fromTo("#strike",{{scaleX:0}},{{scaleX:1,duration:0.25,ease:"power2.out"}},{n8-0.1});',
          f'tl.to("#n600",{{opacity:0.45,duration:0.2}},{n8});',
          f'tl.fromTo("#n800",{{scale:3,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"power4.in"}},{n8-0.3});',
          f'tl.fromTo("#numcard",{{x:-10}},{{x:0,duration:0.06,repeat:5,yoyo:true}},{n8});',
          f'tl.to("#numcard",{{y:80,opacity:0,duration:0.25,ease:"power2.in"}},{n1-0.25});']
S("whoosh", n6, 0.45)
S("impact-bass-2", n8, 0.28)
S("ping", n8 + 0.05, 0.35)

# 5 — KENAPA?
k0, k1 = o(36.14), o(37.20)
clip("why", k0, k1, '<div class="big-q" id="kq">KENAPA<span class="yl">?</span></div>', "ov mid")
ov_js += [f'tl.fromTo("#kq",{{scale:0.3,rotation:-8,opacity:0}},{{scale:1,rotation:0,opacity:1,duration:0.35,ease:"back.out(3)"}},{k0});']
S("pop", k0 + 0.1, 0.55)

# 6 — panas + jerebu chips, 7 — kipas + aircond pagi -> malam
c0, c1 = o(40.70), o(43.55)
clip("weather", c0, c1,
     f'<div class="chips"><div class="chip" id="chSun">{ic("sun")}CUACA PANAS</div><div class="chip" id="chHaze">{ic("haze")}JEREBU</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#chSun",{{x:-700}},{{x:0,duration:0.35,ease:"back.out(1.4)"}},{o(40.84)-0.15});',
          f'tl.fromTo("#chSun svg",{{rotation:0}},{{rotation:90,duration:2.7,ease:"none"}},{o(40.84)});',
          f'tl.fromTo("#chHaze",{{x:700}},{{x:0,duration:0.35,ease:"back.out(1.4)"}},{o(42.16)-0.15});']
S("whoosh-short", o(40.84) - 0.05, 0.35)
S("whoosh-short", o(42.16) - 0.05, 0.35)
f0, f1 = o(45.10), o(49.45)
clip("fan", f0, f1,
     f'<div class="chips"><div class="chip" id="chFan">{ic("fan")}KIPAS</div><div class="chip" id="chAc">{ic("ac")}AIRCOND</div>'
     f'<div class="chip wide" id="chTime">PAGI <span class="yl">→</span> MALAM</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#chFan",{{scale:0}},{{scale:1,duration:0.3,ease:"back.out(2)"}},{f0});',
          f'tl.fromTo("#chFan svg",{{rotation:0}},{{rotation:1440,duration:{f1-f0:.2f},ease:"none"}},{f0});',
          f'tl.fromTo("#chAc",{{scale:0}},{{scale:1,duration:0.3,ease:"back.out(2)"}},{o(46.10)});',
          f'tl.fromTo("#chTime",{{y:60,opacity:0}},{{y:0,opacity:1,duration:0.3}},{o(47.74)});']
S("pop", f0, 0.4)
S("pop", o(46.10), 0.4)
S("click", o(47.74), 0.4)

# 8 — +200 kWj ruang tambahan
r0, r1 = o(51.76), o(55.75)
clip("extra", r0, r1,
     '<div class="card" id="extracard"><div class="lbl">RUANG TAMBAHAN</div><div class="plus"><span class="yl">+200</span> kWj</div><div class="unit">sehingga 800 kWj sebulan</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#extracard",{{scale:0.5,opacity:0}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(2.2)"}},{o(52.06)-0.1});',
          f'tl.to("#extracard",{{opacity:0,y:60,duration:0.2}},{r1-0.2});']
S("ping", o(52.06), 0.4)

# section transition 1
sec2 = o(65.00)
S("whoosh", sec2, 0.5)

# 9 — APA KORANG DAPAT?
a0, a1 = o(65.08), o(68.70)
clip("ask", a0, a1, '<div class="tag big" id="askin">APA KORANG DAPAT?</div>', "ov top")
ov_js += [f'tl.fromTo("#askin",{{y:-200}},{{y:0,duration:0.4,ease:"back.out(1.6)"}},{a0});']

# 10+11 — dikecualikan 3 caj checklist
x0, x1 = o(68.76), o(91.86)
rows = [("AFA", "Pelarasan Kos Bahan Api Automatik", 81.50), ("CAJ PERUNCITAN", "Retail charge", 87.90), ("SST", "Cukai jualan & perkhidmatan", 91.14)]
rows_html = "".join(
    f'<div class="row" id="row{i}"><span class="rn">{i+1}</span><div class="rt"><div class="rh">{h}</div><div class="rs">{s}</div></div><span class="rc" id="rc{i}">{ICON["check"]}</span></div>'
    for i, (h, s, _) in enumerate(rows))
clip("exempt", x0, x1 + 0.6,
     f'<div class="card list" id="listcard"><div class="lbl">GUNA ≤ 800 kWj SEBULAN?</div><div class="ttl">DIKECUALIKAN <span class="yl" id="three">3</span> CAJ</div>{rows_html}</div>', "ov mid")
ov_js += [f'tl.fromTo("#listcard",{{y:140,opacity:0}},{{y:0,opacity:1,duration:0.4,ease:"power3.out"}},{x0});',
          
          f'tl.fromTo("#three",{{scale:2.5}},{{scale:1,duration:0.35,ease:"back.out(3)"}},{o(75.46)});']
for i, (_, _, st) in enumerate(rows):
    at = o(st) - 0.2
    ov_js += [f'tl.fromTo("#row{i}",{{opacity:0.18,scale:0.96}},{{opacity:1,scale:1,duration:0.3,ease:"power3.out"}},{at});',
              f'tl.fromTo("#rc{i}",{{scale:0}},{{scale:1,duration:0.3,ease:"back.out(3)"}},{at+0.35});']
    S("whoosh-short", at + 0.1, 0.3)
    S("pop", at + 0.4, 0.5)
ov_js.append(f'tl.to("#listcard",{{opacity:0,scale:0.9,duration:0.25}},{x1+0.35});')
S("pop", o(75.46), 0.4)

# 12 — lebih ramai isi rumah dilindungi
p0, p1 = o(92.30), o(95.10)
clip("prot", p0, p1, f'<div class="card" id="protcard">{ic("house","ico big")}<div class="ttl sm">LEBIH RAMAI<br><span class="yl">ISI RUMAH DILINDUNGI</span></div></div>', "ov mid")
ov_js += [f'tl.fromTo("#protcard",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(2)"}},{p0});']
S("chime", p0, 0.35)

# section transition 2
sec3 = o(133.15)
S("whoosh", sec3, 0.5)

# 13 — INGAT! berhemah, jimat = jimat duit
i0, i1 = o(133.20), o(142.00)
clip("ingat", i0, i1, f'<div class="tag big warn" id="ingin">{ic("warn")}INGAT!</div>', "ov top")
ov_js += [f'tl.fromTo("#ingin",{{scale:0,rotation:-10}},{{scale:1,rotation:0,duration:0.35,ease:"back.out(3)"}},{i0});',
          f'tl.to("#ingin",{{scale:1.06,duration:0.3,yoyo:true,repeat:5,ease:"sine.inOut"}},{i0+0.4});']
S("notification", i0, 0.35)
b0 = o(139.90)
clip("hemah", b0, i1, '<div class="card" id="hemcard"><div class="lbl">GUNA ELEKTRIK SECARA</div><div class="ttl">BERHEMAH</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#hemcard",{{y:100,opacity:0}},{{y:0,opacity:1,duration:0.35,ease:"power3.out"}},{b0});']
S("whoosh-short", b0, 0.35)
j0, j1 = o(142.65), o(145.30)
clip("jimat", j0, j1 + 0.2,
     f'<div class="card" id="jimcard"><div class="eq"><span>JIMAT ELEKTRIK</span><span class="yl">=</span><span>JIMAT DUIT</span></div>'
     f'<div class="coins">{ic("coin","c c1")}{ic("coin","c c2")}{ic("coin","c c3")}</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#jimcard",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.35,ease:"back.out(2)"}},{j0});']
for k, d in enumerate([0.9, 1.15, 1.4]):
    ov_js.append(f'tl.fromTo("#jimcard .c{k+1}",{{y:-260,opacity:0}},{{y:0,opacity:1,duration:0.35,ease:"bounce.out"}},{j0+d});')
    S("ping", j0 + d + 0.2, 0.25)

# section transition 3
sec4 = o(199.45)
S("whoosh", sec4, 0.5)

# 14 — KESIMPULAN
z0, z1 = o(199.55), o(211.68)
clip("kes", z0, z1, '<div class="tag big" id="kesin">KESIMPULAN</div>', "ov top")
ov_js += [f'tl.fromTo("#kesin",{{y:-200}},{{y:0,duration:0.4,ease:"back.out(1.6)"}},{z0});']
q0 = o(201.68)
clip("pantau", q0, o(205.10), f'<div class="card" id="pancard"><div class="lbl">KERAJAAN TERUS PANTAU</div><div class="ttl sm">KOS BAHAN API<br>&amp; PASARAN TENAGA</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#pancard",{{x:900}},{{x:0,duration:0.35,ease:"power3.out"}},{q0});',
          f'tl.to("#pancard",{{x:-900,duration:0.25,ease:"power3.in"}},{o(205.10)-0.25});']
S("whoosh-short", q0, 0.35)
q1 = o(205.10)
clip("seimbang", q1, z1,
     f'<div class="card" id="balcard"><div class="lbl">TARIF ELEKTRIK SEIMBANG</div>{ic("scale","ico big")}'
     f'<div class="bal"><span>KEMAMPUAN<br>RAKYAT</span><span>KESTABILAN<br>BEKALAN</span></div></div>', "ov mid")
ov_js += [f'tl.fromTo("#balcard",{{x:900}},{{x:0,duration:0.35,ease:"power3.out"}},{q1});',
          f'tl.fromTo("#balcard svg",{{rotation:-12}},{{rotation:0,duration:1.4,ease:"elastic.out(1,0.3)"}},{o(206.34)});']
S("whoosh-short", q1, 0.35)

# 15 — recap 600 -> 800
m0, m1 = o(212.82), o(219.78)
clip("recap", m0, m1,
     '<div class="card numcard" id="reccard"><div class="nums"><div class="old" id="r600">600<s id="rstrike"></s></div><div class="arr2">→</div><div class="new" id="r800">800</div></div>'
     '<div class="unit">kWj / sebulan</div><div class="sub" id="recsub">LEBIH RAMAI ISI RUMAH DILINDUNGI</div></div>', "ov mid")
ov_js += [f'tl.fromTo("#reccard",{{y:120,opacity:0}},{{y:0,opacity:1,duration:0.35,ease:"power3.out"}},{m0});',
          f'tl.fromTo("#rstrike",{{scaleX:0}},{{scaleX:1,duration:0.25}},{o(215.58)-0.1});',
          f'tl.to("#r600",{{opacity:0.45,duration:0.2}},{o(215.58)});',
          f'tl.fromTo("#r800",{{scale:3,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"power4.in"}},{o(215.58)-0.3});',
          f'tl.fromTo("#recsub",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3}},{o(216.74)});']
S("impact-bass-1", o(215.58), 0.22)

# 16 — ringankan beban rakyat
g0 = o(222.80)
clip("beban", g0, o(224.00), '<div class="tag big" id="bebin">RINGANKAN BEBAN RAKYAT</div>', "ov top")
ov_js += [f'tl.fromTo("#bebin",{{scale:0.5,opacity:0}},{{scale:1,opacity:1,duration:0.3,ease:"back.out(2)"}},{g0});']
S("pop", g0, 0.4)

# 17 — CTA share + terima kasih
s0, s_end = o(224.00), TOTAL
clip("cta", s0, s_end,
     f'<div class="cta" id="ctain">{ic("share","ico")}<span>SHARE</span></div><div class="cta-sub" id="ctasub">dengan family &amp; kawan-kawan</div>'
     f'<div class="ty" id="ty">TERIMA KASIH!</div>', "ov mid")
ov_js += [f'tl.fromTo("#ctain",{{scale:0,rotation:-6}},{{scale:1,rotation:0,duration:0.4,ease:"back.out(2.5)"}},{s0});',
          f'tl.to("#ctain",{{scale:1.08,duration:0.25,yoyo:true,repeat:3,ease:"sine.inOut"}},{s0+0.5});',
          f'tl.fromTo("#ctasub",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3}},{o(225.08)});',
          f'tl.fromTo("#ty",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.35,ease:"back.out(2)"}},{o(227.12)});']
S("pop", s0 + 0.1, 0.5)
S("chime", o(227.12), 0.35)

# ---------------------------------------------------------------- camera (jump-cut punch-ins)
cam_js = []
for (a, b, z), s in zip(PIECES, starts):
    cam_js.append(f'tl.set("#cam",{{scale:{z}}},{s});')
for sec in (sec2, sec3, sec4):  # section transitions: zoom-blur + flash
    cam_js.append(f'tl.set("#cam",{{scale:1.3,filter:"blur(10px)"}},{sec});')
    cam_js.append(f'tl.to("#cam",{{scale:1.04,filter:"blur(0px)",duration:0.35,ease:"power3.out"}},{sec});')
    cam_js.append(f'tl.set("#flash",{{opacity:0.7}},{sec});')
    cam_js.append(f'tl.to("#flash",{{opacity:0,duration:0.3}},{sec});')
for at in (n8, o(215.58)):  # emphasis punch on the 800 reveal
    cam_js.append(f'tl.set("#cam",{{scale:1.18}},{at});')
    cam_js.append(f'tl.to("#cam",{{scale:1.08,duration:0.5,ease:"power2.out"}},{at});')

# ---------------------------------------------------------------- assemble
vid_html = "\n".join(
    f'<video id="v{i}" class="vid" src="assets/source.mp4" data-start="{s:.3f}" data-duration="{(starts[i+1] if i+1<len(starts) else TOTAL)-s:.3f}" data-media-start="{a:.3f}" data-track-index="{i % 2}" playsinline data-has-audio="true"></video>'
    for i, ((a, b, _), s) in enumerate(zip(PIECES, starts)))
sfx_html = "\n".join(
    f'<audio id="sfx{i}" src="assets/sfx/{n}.mp3" data-start="{st:.3f}" data-duration="{min(d, TOTAL-st):.3f}" data-track-index="{20+i}" data-volume="{v}"></audio>'
    for i, (n, st, d, v) in enumerate(sfx))

def fill(name, **kv):
    txt = open(os.path.join(HERE, name)).read().replace("{{TOTAL}}", f"{TOTAL:.3f}")
    for k, v in kv.items():
        txt = txt.replace("{{%s}}" % k, v)
    return txt


os.makedirs(os.path.join(ROOT, "compositions"), exist_ok=True)
open(os.path.join(ROOT, "index.html"), "w").write(fill(
    "template.html", VIDEOS=vid_html, SFX=sfx_html,
    JS="\n".join(cam_js) + f'\ntl.fromTo("#prog",{{scaleX:0}},{{scaleX:1,duration:{TOTAL:.3f},ease:"none"}},0);'))
open(os.path.join(ROOT, "compositions", "gfx.html"), "w").write(fill("gfx_template.html", OVERLAYS="\n".join(ov_html), JS="\n".join(ov_js)))
open(os.path.join(ROOT, "compositions", "caps.html"), "w").write(fill("caps_template.html", CAPTIONS="\n".join(cap_html), JS="\n".join(cap_js)))
json.dump({"total": TOTAL, "pieces": [dict(src_in=a, src_out=b, out_start=s) for (a, b, _), s in zip(PIECES, starts)]},
          open(os.path.join(HERE, "edl.json"), "w"), indent=1)
print("duration", TOTAL, "pieces", len(PIECES), "captions", len(chunks), "sfx", len(sfx))
