"""Generate index.html from tools/edl.json.
Run from the project root: python3 -I tools/build.py"""
import json, html

E = json.load(open("tools/edl.json"))
TOTAL = E["total"]
SEG = {s["id"]: s for s in E["edl"]}

def T(x):
    """map a time on the all-1x timeline to the real (speed-adjusted) timeline"""
    if x >= 88.5:  # cues after the sweep were authored when sapu-2 ran to 119.35 (0.25s longer)
        x -= 0.25
    for e in E["edl"]:
        d1 = e["mo"] - e["mi"]
        if e["start1x"] - 1e-6 <= x < e["start1x"] + d1 + 1e-6:
            return round(e["start"] + (x - e["start1x"]) / e["rate"], 3)
    return TOTAL

import re
POS = re.compile(r", (-?\d+(?:\.\d+)?)\);$")
def remap_js(line):
    return POS.sub(lambda m: f", {T(float(m.group(1)))});", line)

YEL, NAVY, GRN, RED, WHT = "#FFD60A", "#0A1A3A", "#22C55E", "#FF3B3B", "#FFFFFF"

# ---------------------------------------------------------------- video
# scale per segment (punch-ins hide jump cuts); (time, scale) keys are output seconds
PUNCH = {
    "c0": [(0, 1.32, 1.14, 3.7)],                    # hook: push-out settle
    "c1": [(3.70, 1.0, 1.0, 0), (8.45, 1.14, 1.14, 0), (12.45, 1.0, 1.0, 0)],
    "c2": [(19.20, 1.12, 1.12, 0), (24.75, 1.32, 1.32, 0), (26.75, 1.12, 1.12, 0)],
    "c3": [(28.50, 1.0, 1.0, 0)],
    "c4": [(33.15, 1.16, 1.16, 0)],
    "c5": [(37.50, 1.0, 1.0, 0), (40.35, 1.18, 1.18, 0)],
    "c6": [(42.60, 1.0, 1.0, 0), (49.45, 1.15, 1.15, 0), (53.75, 1.0, 1.0, 0)],
    "c7": [(62.55, 1.12, 1.12, 0), (68.85, 1.0, 1.0, 0), (74.0, 1.15, 1.15, 0)],
    "c8": [(77.20, 1.0, 1.0, 0)],
    "c9": [(84.65, 1.0, 1.0, 0)],
    "c10": [(88.50, 1.0, 1.0, 0)],
    "c11": [(94.80, 1.14, 1.14, 0), (102.3, 1.0, 1.0, 0), (105.3, 1.18, 1.18, 0)],
    "c12": [(108.45, 1.28, 1.28, 0)],
    "c13": [(109.45, 1.0, 1.0, 0), (114.0, 1.12, 1.12, 0), (122.2, 1.0, 1.0, 0), (129.7, 1.12, 1.12, 0), (133.7, 1.0, 1.0, 0)],
}
vids, js = [], []
for s in E["edl"]:
    i = s["id"]
    vids.append(f'''      <div class="vw" id="vw-{i}"><video id="{i}" class="clip vid" src="assets/footage/{s["src"]}.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" data-media-start="{s["mi"]}"{f' data-playback-rate="{s["rate"]}"' if s["rate"] != 1 else ""} data-track-index="0" playsinline data-has-audio="true" data-audio-group="voice"></video></div>''')
    for t, a, b, d in PUNCH[i]:
        if d:
            js.append(f'tl.fromTo("#vw-{i}", {{scale:{a}}}, {{scale:{b}, duration:{d}, ease:"power2.out"}}, {T(t)});')
        else:
            js.append(f'tl.set("#vw-{i}", {{scale:{a}}}, {T(t)});')

# ---------------------------------------------------------------- sfx
SFX_DUR = {"impact-bass-1": 2.12, "impact-bass-2": 2.59, "whoosh": .57, "whoosh-short": .57, "pop": .72,
           "sparkle": 1.8, "click": .37, "click-soft": .37, "ping": 1.32, "chime": 2.5, "notification": 2.46,
           "whoosh-cinematic": 5.54, "glitch-3": 3.1, "riser": 10.03}
SFX = [  # (output time, file, volume)
    (0.10, "impact-bass-1", .55), (0.12, "whoosh", .35),
    (3.80, "pop", .45), (6.60, "sparkle", .35),
    (8.50, "whoosh-short", .35), (13.55, "click", .4), (16.45, "click", .4),
    (18.65, "whoosh", .35), (22.30, "ping", .35), (24.62, "impact-bass-2", .5),
    (27.75, "pop", .5), (30.55, "pop", .4), (31.95, "pop", .4),
    (33.15, "whoosh-short", .3), (35.75, "click-soft", .45), (36.35, "click-soft", .45),
    (38.70, "chime", .3),
    (42.60, "whoosh", .4), (42.90, "pop", .45), (44.2, "sparkle", .25),
    (49.50, "pop", .45), (53.80, "whoosh-short", .35), (59.00, "ping", .3),
    (63.00, "click", .45), (68.90, "click", .45), (72.40, "click", .45),
    (74.05, "chime", .3),
    (77.20, "whoosh", .35), (77.45, "pop", .35), (92.55, "notification", .35),
    (102.40, "whoosh-short", .3), (105.30, "ping", .35),
    (108.40, "whoosh", .4), (108.55, "impact-bass-1", .35),
    (110.50, "whoosh-short", .3), (114.10, "pop", .35), (122.30, "whoosh-short", .3), (125.15, "impact-bass-2", .4),
    (129.80, "sparkle", .3), (133.80, "notification", .35),
]
sfx_html = []
for n, (t, f, v) in enumerate(SFX):
    t = T(t)
    d = min(SFX_DUR[f], TOTAL - t)
    sfx_html.append(f'      <audio id="sfx{n}" src="assets/sfx/{f}.mp3" data-start="{t}" data-duration="{d:.2f}" data-track-index="{9 + n % 2}" data-volume="{v}"></audio>')

# ---------------------------------------------------------------- music bed (santai)
import os
music_html = ""
if os.path.exists("assets/music/bed.mp3"):
    UNDER, LIFT = 0.30, 0.62          # under speech / during mangga + sapu (no talking)
    pts = [(0, 0.0), (0.6, UNDER)]
    for a, b in ((T(42.6), T(49.45)), (T(77.2), T(88.75))):
        pts += [(a, UNDER), (a + .5, LIFT), (b - .5, LIFT), (b, UNDER)]
    pts += [(TOTAL - 1.6, UNDER), (TOTAL, 0.0)]
    lane = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [{"t": round(t, 3), "v": v} for t, v in pts]}]}, separators=(",", ":"))
    music_html = f"""      <audio id="music-bed" src="assets/music/bed.mp3" data-start="0" data-duration="{TOTAL}" data-track-index="11" data-volume="1" data-automation='{lane}'></audio>"""

# ---------------------------------------------------------------- graphics
G = []  # (id, start, end, inner_html, js_lines(t0)->list)
def card(gid, a, b, inner, anim=None, cls="top"):
    G.append((gid, a, b, inner, anim, cls))

def pop_in(sel, t, y=40, d=.45):
    return f'tl.fromTo("{sel}", {{opacity:0, y:{y}, scale:.86}}, {{opacity:1, y:0, scale:1, duration:{d}, ease:"back.out(2)"}}, {t});'
def out(sel, t, d=.25):
    return f'tl.to("{sel}", {{opacity:0, y:-20, duration:{d}, ease:"power2.in"}}, {t});'

# icons (inline svg, no emoji fonts in headless chrome)
BOLT = '<svg viewBox="0 0 24 24" class="ico"><path d="M13 2 4 14h7l-1 8 9-12h-7z" fill="currentColor"/></svg>'
CHECK = '<svg viewBox="0 0 24 24" class="ico"><path d="M4 12.5 9.5 18 20 6.5" stroke="currentColor" stroke-width="3.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
SHIELD = '<svg viewBox="0 0 24 24" class="ico"><path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5z" fill="currentColor"/><path d="M8 12l3 3 5-6" stroke="#0A1A3A" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>'
CAL = '<svg viewBox="0 0 24 24" class="ico"><rect x="3" y="5" width="18" height="16" rx="3" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M3 10h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'
SUN = '<svg viewBox="0 0 24 24" class="ico"><circle cx="12" cy="12" r="5" fill="currentColor"/><g stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3M4.6 4.6l2.1 2.1M17.3 17.3l2.1 2.1M4.6 19.4l2.1-2.1M17.3 6.7l2.1-2.1"/></g></svg>'
FAN = '<svg viewBox="0 0 24 24" class="ico"><circle cx="12" cy="12" r="2.2" fill="currentColor"/><path d="M12 9.8C11 6 12 2.5 15 3c2.6.5 1.6 4.6-3 6.8zM14.2 12c3.8-1 7.3 0 6.8 3-.5 2.6-4.6 1.6-6.8-3zM12 14.2c1 3.8 0 7.3-3 6.8-2.6-.5-1.6-4.6 3-6.8zM9.8 12C6 13 2.5 12 3 9c.5-2.6 4.6-1.6 6.8 3z" fill="currentColor"/></svg>'
MANGO = '<svg viewBox="0 0 64 64" class="mango"><path d="M33 12c14 2 24 14 22 29-2 13-14 20-26 17C16 55 8 44 11 31c3-12 11-20 22-19z" fill="#FFB020"/><path d="M33 12c6 1 11 4 15 9-8-3-16-1-22 5 0-6 2-11 7-14z" fill="#FFCF4A" opacity=".8"/><path d="M33 12c-1-4 1-7 4-9" stroke="#5B3A1A" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M37 5c6-3 13-1 16 4-7 2-13 1-16-4z" fill="#2E9E4F"/></svg>'
BROOM = '<svg viewBox="0 0 24 24" class="ico"><path d="M19 2 11 12" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M9 11l4 4-2 7c-3-1-6-3-8-6l6-5z" fill="currentColor"/></svg>'
BULB = '<svg viewBox="0 0 24 24" class="ico"><path d="M12 2a7 7 0 0 0-4 12.7V18h8v-3.3A7 7 0 0 0 12 2z" fill="currentColor"/><rect x="8.5" y="19.2" width="7" height="2.6" rx="1.2" fill="currentColor"/></svg>'
SCALE = '<svg viewBox="0 0 24 24" class="ico"><path d="M12 3v18M6 21h12M4 7h16" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M4 7l-3 7a3.5 3.5 0 0 0 6 0zM20 7l-3 7a3.5 3.5 0 0 0 6 0z" fill="currentColor"/></svg>'
SHARE = '<svg viewBox="0 0 24 24" class="ico"><circle cx="18" cy="5" r="3" fill="currentColor"/><circle cx="6" cy="12" r="3" fill="currentColor"/><circle cx="18" cy="19" r="3" fill="currentColor"/><path d="M8.6 10.7l6.8-4M8.6 13.3l6.8 4" stroke="currentColor" stroke-width="2.2"/></svg>'
ALERT = '<svg viewBox="0 0 24 24" class="ico"><path d="M12 2 1 21h22z" fill="currentColor"/><path d="M12 9v5M12 17.2v.3" stroke="#0A1A3A" stroke-width="2.6" stroke-linecap="round"/></svg>'

# --- HOOK
card("g-hook", 0.0, 3.75, f'''
  <div class="hook">
    <div class="hook-l1" id="hk1"><span class="bolt">{BOLT}</span>BIL ELEKTRIK</div>
    <div class="hook-l2" id="hk2">NAIK MENDADAK?</div>
  </div>''', lambda a, b: [
    'tl.fromTo("#hk1", {opacity:0, scale:2.2, rotation:-6}, {opacity:1, scale:1, rotation:-3, duration:.32, ease:"power4.out"}, 0.08);',
    'tl.fromTo("#hk2", {opacity:0, scale:2.4, rotation:5}, {opacity:1, scale:1, rotation:2, duration:.32, ease:"power4.out"}, 0.42);',
    'tl.to("#g-hook .hook", {keyframes:{x:[0,-16,14,-10,8,-4,0]}, duration:.42, ease:"none"}, 0.5);',
    'tl.to("#hk2", {scale:1.06, duration:.5, yoyo:true, repeat:3, ease:"sine.inOut"}, 1.0);',
    out("#g-hook .hook", b - .25)])

card("g-stres", 3.75, 5.6, '<div class="sticker yel" id="st1">JANGAN STRES!</div>',
     lambda a, b: [f'tl.fromTo("#st1", {{opacity:0, scale:.3, rotation:-18}}, {{opacity:1, scale:1, rotation:-5, duration:.4, ease:"back.out(2.6)"}}, {a+.05});', out("#st1", b-.2)])

card("g-baik", 5.75, 8.4, f'<div class="badge grn" id="bk1">{CHECK}<span>ADA BERITA BAIK!</span></div>',
     lambda a, b: [pop_in("#bk1", a+.1), f'tl.fromTo("#bk1 .ico", {{scale:0, rotation:-90}}, {{scale:1, rotation:0, duration:.4, ease:"back.out(3)"}}, {a+.35});', out("#bk1", b-.25)])

card("g-madani", 8.45, 12.4, '''
  <div class="panel" id="md1"><div class="kicker">LANGKAH SEGERA</div><div class="big">KERAJAAN MADANI</div></div>''',
     lambda a, b: [f'tl.fromTo("#md1", {{opacity:0, x:-120}}, {{opacity:1, x:0, duration:.45, ease:"power3.out"}}, {a+.05});',
                   f'tl.fromTo("#md1 .kicker", {{opacity:0, y:10}}, {{opacity:1, y:0, duration:.3}}, {a+.3});', out("#md1", b-.25)])

card("g-date", 12.45, 18.55, f'''
  <div class="panel" id="dt1"><div class="kicker">{CAL}<span>TEMPOH PERLINDUNGAN</span></div>
    <div class="dates"><div class="dbox" id="dt-a">SEPT<b>2026</b></div><div class="arrow" id="dt-ar">&#8594;</div><div class="dbox" id="dt-b">31 DIS<b>2026</b></div></div></div>''',
     lambda a, b: [pop_in("#dt1", a+.05), pop_in("#dt-a", 13.55, 20, .35),
                   'tl.fromTo("#dt-ar", {opacity:0, x:-30}, {opacity:1, x:0, duration:.3}, 15.25);',
                   pop_in("#dt-b", 16.45, 20, .35), out("#dt1", b-.25)])

def meter(gid, a, b, t600, t800, title, sub, cls="top"):
    card(gid, a, b, f'''
  <div class="panel meter" id="{gid}-p"><div class="kicker">{BOLT}<span>{title}</span></div>
    <div class="num"><span class="n" id="{gid}-n">600</span><span class="unit">kWh<i>/bulan</i></span></div>
    <div class="bar"><div class="fill" id="{gid}-f"></div><div class="mark" style="left:75%"></div></div>
    <div class="sub" id="{gid}-s">{sub}</div></div>''',
         lambda a, b: [pop_in(f"#{gid}-p", a+.05),
                       f'tl.fromTo("#{gid}-f", {{width:"0%"}}, {{width:"75%", duration:.6, ease:"power2.out"}}, {t600});',
                       f'tl.fromTo("#{gid}-n", {{opacity:0}}, {{opacity:1, duration:.2}}, {t600});',
                       f'const {gid.replace("-","_")}c = {{v:600}};',
                       f'tl.to({gid.replace("-","_")}c, {{v:800, duration:.7, ease:"power3.out", onUpdate:()=>{{document.getElementById("{gid}-n").textContent=Math.round({gid.replace("-","_")}c.v)}}}}, {t800});',
                       f'tl.to("#{gid}-f", {{width:"100%", backgroundColor:"{GRN}", duration:.7, ease:"power3.out"}}, {t800});',
                       f'tl.fromTo("#{gid}-n", {{scale:1}}, {{scale:1.22, color:"{YEL}", duration:.18, yoyo:true, repeat:1, ease:"power2.out"}}, {t800+.55});',
                       f'tl.fromTo("#{gid}-s", {{opacity:0, y:12}}, {{opacity:1, y:0, duration:.35}}, {t800+.4});',
                       out(f"#{gid}-p", b-.25)], cls=cls)

# set number text at seek-start so scrubbing backwards restores "600"
meter("g-m1", 18.65, 26.75, 22.3, 24.75, "PERLINDUNGAN BIL ELEKTRIK DOMESTIK", "+200 kWh SEBULAN")

card("g-kenapa", 27.7, 28.55, '<div class="sticker red" id="kn1">KENAPA?</div>',
     lambda a, b: [f'tl.fromTo("#kn1", {{opacity:0, scale:1.5}}, {{opacity:1, scale:1, duration:.22, ease:"power4.out"}}, {a});'])

card("g-panas", 30.3, 33.1, f'''<div class="chips"><div class="chip red" id="pn1">{SUN}<span>CUACA PANAS GILA</span></div><div class="chip gry" id="pn2"><span>+ JEREBU</span></div></div>''',
     lambda a, b: [pop_in("#pn1", 30.5, 20, .35), pop_in("#pn2", 31.9, 20, .35),
                   'tl.to("#pn1 .ico", {rotation:180, duration:2.6, ease:"none"}, 30.5);', out("#g-panas .chips", b-.2)])

card("g-aircon", 33.15, 37.4, f'''
  <div class="panel" id="ac1"><div class="row"><span class="fan">{FAN}</span><div class="big">KIPAS + AIRCON</div></div>
  <div class="tl"><span id="ac-p">PAGI</span><div class="line"><div class="lf" id="ac-l"></div></div><span id="ac-m">MALAM</span></div></div>''',
     lambda a, b: [pop_in("#ac1", a+.05), 'tl.to("#ac1 .fan .ico", {rotation:1440, duration:4.2, ease:"none"}, 33.2);',
                   'tl.fromTo("#ac-l", {width:"0%"}, {width:"100%", duration:.7, ease:"power1.inOut"}, 35.75);',
                   pop_in("#ac-p", 35.7, 10, .25), pop_in("#ac-m", 36.35, 10, .25), out("#ac1", b-.25)])

card("g-tambah", 38.6, 42.55, f'''
  <div class="panel" id="tb1"><div class="kicker">RUANG TAMBAHAN</div><div class="huge"><span class="y">800</span> kWh<i>/bulan</i></div></div>''',
     lambda a, b: [pop_in("#tb1", a+.05), f'tl.fromTo("#tb1 .y", {{scale:.5}}, {{scale:1, duration:.4, ease:"back.out(3)"}}, 40.35);', out("#tb1", b-.25)])

card("g-mangga", 42.6, 49.45, f'''
  <div class="mg-wrap"><div class="sticker yel mg" id="mg1"><span>JAP&#8230; JOLOK MANGGA DULU</span></div><div id="mg-ic">{MANGO}</div></div>''',
     lambda a, b: [f'tl.fromTo("#mg1", {{opacity:0, scale:.4, rotation:12}}, {{opacity:1, scale:1, rotation:3, duration:.45, ease:"back.out(2.4)"}}, {a+.3});',
                   f'tl.fromTo("#mg-ic", {{opacity:0, y:-260, rotation:-40}}, {{opacity:1, y:0, rotation:0, duration:.7, ease:"bounce.out"}}, {a+.6});',
                   f'tl.to("#mg-ic", {{rotation:12, duration:.6, yoyo:true, repeat:7, ease:"sine.inOut"}}, {a+1.3});',
                   out("#g-mangga .mg-wrap", b-.3)])

card("g-apa", 49.5, 53.7, '<div class="panel q" id="ap1"><div class="big">APA KORANG DAPAT?</div></div>',
     lambda a, b: [pop_in("#ap1", a+.05), out("#ap1", b-.2)])

card("g-3caj", 53.8, 74.0, f'''
  <div class="panel list" id="cj1">
    <div class="lhead"><div class="cond" id="cj-c">GUNA <span class="y">800 kWh</span> KE BAWAH?</div>
    <div class="kicker" id="cj-k">DIKECUALIKAN DARIPADA 3 CAJ</div></div>
    <div class="item" id="cj-1"><span class="tick">{CHECK}</span><div><b>CAJ AFA</b><small id="cj-1s">Pelarasan Kos Bahan Api Automatik</small></div></div>
    <div class="item" id="cj-2"><span class="tick">{CHECK}</span><div><b>CAJ PERUNCITAN</b></div></div>
    <div class="item" id="cj-3"><span class="tick">{CHECK}</span><div><b>CAJ SST</b></div></div>
  </div>''',
     lambda a, b: [pop_in("#cj1", a+.05), pop_in("#cj-c", a+.15, 14, .35),
                   'tl.fromTo("#cj-k", {opacity:0, y:12}, {opacity:1, y:0, duration:.35}, 58.95);',
                   pop_in("#cj-1", 63.0, 16, .35), 'tl.fromTo("#cj-1s", {opacity:0}, {opacity:1, duration:.3}, 64.5);',
                   pop_in("#cj-2", 68.9, 16, .35), pop_in("#cj-3", 72.4, 16, .35),
                   *[f'tl.fromTo("#cj-{k} .tick", {{scale:0, rotation:-120}}, {{scale:1, rotation:0, duration:.4, ease:"back.out(3)"}}, {t+.1});' for k, t in ((1, 63.0), (2, 68.9), (3, 72.4))],
                   out("#cj1", b-.25)], cls="bot")

card("g-lindung", 74.0, 77.15, f'''<div class="badge grn big2" id="ld1">{SHIELD}<span>LEBIH RAMAI ISI RUMAH DILINDUNGI</span></div>''',
     lambda a, b: [pop_in("#ld1", a+.05), f'tl.fromTo("#ld1 .ico", {{scale:0}}, {{scale:1, duration:.45, ease:"back.out(3)"}}, {a+.3});', out("#ld1", b-.2)])

card("g-sapu", 77.3, 84.6, f'<div class="tag" id="sp1">{BROOM}<span>SAMBIL SAPU SAMPAH&#8230;</span></div>',
     lambda a, b: [f'tl.fromTo("#sp1", {{opacity:0, x:-200}}, {{opacity:1, x:0, duration:.45, ease:"back.out(1.8)"}}, {a+.1});',
                   f'tl.to("#sp1 .ico", {{rotation:-25, duration:.35, yoyo:true, repeat:9, ease:"sine.inOut"}}, {a+.5});', out("#sp1", b-.3)])

card("g-pesan", 92.5, 95.4, f'<div class="badge red" id="ps1">{ALERT}<span>PESANAN PENTING</span></div>',
     lambda a, b: [pop_in("#ps1", a+.05), 'tl.to("#ps1", {keyframes:{x:[0,-10,9,-6,4,0]}, duration:.36, ease:"none"}, 92.7);', out("#ps1", b-.25)])

card("g-had", 97.3, 102.3, '''<div class="panel" id="hd1"><div class="kicker">WALAUPUN HAD DINAIKKAN KE</div><div class="huge"><span class="y">800</span> kWh<i>/bulan</i></div></div>''',
     lambda a, b: [pop_in("#hd1", a+.05), out("#hd1", b-.25)])

card("g-hemah", 102.4, 105.25, f'''<div class="badge yel" id="hm1">{BULB}<span>GUNA ELEKTRIK SECARA BERHEMAH</span></div>''',
     lambda a, b: [pop_in("#hm1", a+.05), f'tl.fromTo("#hm1 .ico", {{opacity:.4}}, {{opacity:1, duration:.15, yoyo:true, repeat:5}}, {a+.4});', out("#hm1", b-.2)])

card("g-jimat", 105.3, 108.4, '''<div class="eq" id="jm1"><div class="chip yel" id="jm-a"><span>JIMAT ELEKTRIK</span></div><div class="eqs" id="jm-e">=</div><div class="chip grn" id="jm-b"><span>JIMAT DUIT</span></div></div>''',
     lambda a, b: [pop_in("#jm-a", a+.05, 16, .35), pop_in("#jm-e", 106.85, 10, .25), pop_in("#jm-b", 107.55, 16, .35), out("#jm1", b-.2)])

card("g-kesim", 108.45, 110.45, '<div class="band" id="ks1"><span>KESIMPULANNYA</span></div>',
     lambda a, b: ['tl.fromTo("#ks1", {scaleX:0}, {scaleX:1, duration:.35, ease:"power4.out"}, 108.5);',
                   'tl.fromTo("#ks1 span", {opacity:0, scale:.8}, {opacity:1, scale:1, duration:.5, ease:"power3.out"}, 108.65);',
                   'tl.to("#ks1", {scaleX:0, duration:.25, ease:"power2.in"}, 110.15);'], cls="mid")

card("g-pantau", 110.5, 114.0, '''<div class="panel" id="pt1"><div class="kicker">KERAJAAN TERUS PANTAU</div><div class="pills"><span id="pt-a">KOS BAHAN API</span><span id="pt-b">PASARAN TENAGA</span></div></div>''',
     lambda a, b: [pop_in("#pt1", a+.05), pop_in("#pt-a", 110.85, 10, .3), pop_in("#pt-b", 111.25, 10, .3), out("#pt1", b-.2)], cls="bot")

card("g-imbang", 114.05, 121.1, f'''
  <div class="panel" id="im1"><div class="kicker">{SCALE}<span>TARIF SENTIASA SEIMBANG</span></div>
  <div class="beam" id="im-beam"><div class="pan l" id="im-l"><span>KEMAMPUAN</span><span>RAKYAT</span></div><div class="pan r" id="im-r"><span>KESTABILAN</span><span>BEKALAN</span></div></div></div>''',
     lambda a, b: [pop_in("#im1", a+.05), 'tl.fromTo("#im-beam", {rotation:-7}, {rotation:0, duration:1.6, ease:"elastic.out(1,0.35)"}, 116.2);',
                   pop_in("#im-l", 116.95, 10, .3), pop_in("#im-r", 118.15, 10, .3), out("#im1", b-.25)], cls="bot")

meter("g-m2", 122.25, 128.95, 122.9, 125.15, "JADI INGAT YA", "LEBIH RAMAI ISI RUMAH DILINDUNGI", cls="bot")

card("g-ikhtiar", 129.7, 133.7, '''<div class="panel" id="ik1"><div class="kicker">IKHTIAR KERAJAAN MADANI</div><div class="big">RINGANKAN BEBAN RAKYAT</div></div>''',
     lambda a, b: [pop_in("#ik1", a+.05), out("#ik1", b-.2)], cls="bot")

card("g-share", 133.75, TOTAL, f'''
  <div class="cta" id="sh1"><div class="btn" id="sh-b">{SHARE}<span>SHARE VIDEO INI</span></div><div class="ctasub" id="sh-s">dengan family &amp; kawan-kawan</div></div>''',
     lambda a, b: [pop_in("#sh-b", a+.05), 'tl.fromTo("#sh-s", {opacity:0, y:10}, {opacity:1, y:0, duration:.3}, 134.9);',
                   'tl.to("#sh-b", {scale:1.07, duration:.35, yoyo:true, repeat:4, ease:"sine.inOut"}, 135.0);'])

g_html = []
for n, (gid, a, b, inner, anim, cls) in enumerate(G):
    ra, rb = T(a), (TOTAL if b >= TOTAL - 1e-6 else T(b))
    g_html.append(f'      <div id="{gid}" class="clip gfx {cls}" data-start="{ra}" data-duration="{round(rb-ra,3)}" data-track-index="{2 + n % 3}">{inner}\n      </div>')
    if anim:
        js.extend(remap_js(l) for l in anim(a, b))

# ---------------------------------------------------------------- captions
W = E["words"]
chunks, cur = [], []
for i, w in enumerate(W):
    cur.append(w)
    nxt = W[i + 1] if i + 1 < len(W) else None
    txt = " ".join(x[0] for x in cur)
    brk = (nxt is None or len(cur) >= 3 or len(txt) + len(nxt[0]) > 17 or nxt[1] - w[2] > .35
           or w[0][-1] in ",.?" )
    if brk:
        chunks.append(cur); cur = []
CAPGAP_HIDE_1X = [(42.6, 49.45), (53.75, 74.0), (77.2, 94.7), (108.2, 110.5), (110.5, 121.1), (122.25, 133.7)]  # mangga / sapu / section card: no captions
CAPGAP_HIDE = [(T(x), T(y)) for x, y in CAPGAP_HIDE_1X]
cap_html = []
for k, ch in enumerate(chunks):
    a = ch[0][1]
    nxt = chunks[k + 1][0][1] if k + 1 < len(chunks) else TOTAL
    b = min(nxt, ch[-1][2] + .35)
    if b - a < .25: b = a + .25
    if any(x <= a < y for x, y in CAPGAP_HIDE): continue
    for x, y in CAPGAP_HIDE:
        if a < x < b: b = x - .02
    if b - a < .25: continue
    spans = " ".join(f'<span id="w{k}_{j}">{html.escape(x[0].upper().rstrip(",.").replace("KWH","kWh"))}</span>' for j, x in enumerate(ch))
    cap_html.append(f'      <div id="cap{k}" class="clip cap" data-start="{a:.3f}" data-duration="{b-a:.3f}" data-track-index="1"><div class="capin">{spans}</div></div>')
    js.append(f'tl.fromTo("#cap{k} .capin", {{scale:.82, y:18, opacity:0}}, {{scale:1, y:0, opacity:1, duration:.13, ease:"back.out(2.2)"}}, {a:.3f});')
    for j, x in enumerate(ch):
        js.append(f'tl.set("#w{k}_{j}", {{color:"{YEL}"}}, {max(x[1], a):.3f});')
        if j + 1 < len(ch):
            js.append(f'tl.set("#w{k}_{j}", {{color:"{WHT}"}}, {ch[j+1][1]:.3f});')

# ---------------------------------------------------------------- page
CSS = open("tools/style.css").read()
page = f'''<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Perlindungan Bil Elektrik 800 kWh</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
{CSS}
    </style>
  </head>
  <body>
    <!-- GENERATED by tools/build.py from tools/edl.json — edit those, then rebuild -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <!-- track 0: footage (v1 + v2 cut list) -->
{chr(10).join(vids)}
      <div class="vignette"></div>
      <!-- track 1: captions -->
{chr(10).join(cap_html)}
      <!-- tracks 2-4: motion graphics -->
{chr(10).join(g_html)}
      <!-- track 11: music bed -->
{music_html}
      <!-- track 9-10: sound fx -->
{chr(10).join(sfx_html)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + l for l in js).lstrip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open("index.html", "w").write(page)
print("graphics", len(G), "captions", len(cap_html), "sfx", len(SFX), "duration", TOTAL)
