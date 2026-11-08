import re, json, sys, html
src=open(sys.argv[1]).read(); outdir=sys.argv[2]; OFF=4.0
items=[(int(a),float(t),x) for a,t,x in re.findall(r'sec:\s*(\d+),\s*t:\s*([\d.]+),\s*txt:\s*"([^"]+)"',src)]
END=float(re.search(r'AUDIO_END\s*=\s*([\d.]+)',src)[1])
mm=lambda s:f"{int(s//60)}:{s%60:04.1f}"
SEC={0:("Pembukaan","Intro"),1:("1","BUDI MADANI – Kelayakan Dipertingkat"),2:("2","Tiada Sekolah Tercicir"),3:("3","AI Percuma Untuk Anak Muda"),
4:("4","Perkhidmatan Kesihatan Awam Lebih Cekap"),5:("5","e-Invois – Kurangkan Beban Perniagaan Kecil"),6:("6","Bantuan Penjaja & Peniaga Kecil"),7:("Penutup","Penutup")}
VIS={1:["Kad tajuk “1 · BUDI MADANI” atas foto stesen minyak (Ken Burns)","Pil BUDI95 → kotak 200 L ›› 300 L SEBULAN (pop) + “Kelayakan dipertingkat 50%”","Pil BUDI Diesel + kad pick-up & jip → 400 L SEBULAN","Count-up > 16 JUTA (pengguna BUDI95) & > 500,000 (diesel); lencana “Berkuat kuasa 1 September 2026”"],
2:["Kad tajuk “2 · Tiada Sekolah Tercicir” atas foto sekolah","Petikan: pendidikan berkualiti, persekitaran selesa & selamat","Tajuk “Peruntukan penyelenggaraan sekolah” + burst +50%","RM1 BILION ›› RM1.5 BILION, tag “Tahun 2027”","Kad “Melibatkan pelbagai aliran”: SK, SJKC, SJKT, Sekolah Agama, Tahfiz, Pondok, Pendidikan Khas (✓ berperingkat); foto bertukar ke pekerja tapak","Teks besar “Tiada sekolah tercicir daripada arus pembangunan”"],
3:["Kad tajuk “3 · AI Percuma Untuk Anak Muda” atas foto belia","Teks “Anak muda, peneraju masa hadapan negara”","Count-up 100,000 BELIA MALAYSIA + pil “Berusia 18 – 30 tahun”","Teks “Peluang mempelajari teknologi kecerdasan buatan (AI)”","Aliran 2 langkah: Lengkapkan modul ✓ ›› Langganan aplikasi AI PERCUMA → 3 BULAN","Foto anak muda + ikon graf naik: “Generasi muda berdaya saing dalam dunia digital”"],
4:["Kad tajuk “4 · Perkhidmatan Kesihatan Awam Lebih Cekap” atas foto hospital","Teks “Kesihatan rakyat terus menjadi keutamaan”","Reben RM1 BILION + “Memperkukuh pendigitalan sektor kesihatan awam”","Tile count-up 150 HOSPITAL & > 2,000 KLINIK KESIHATAN","Kad Rekod Perubatan Elektronik + ikon Wi-Fi “Capaian internet” + ikon jam randik","✓ Rawatan lebih cepat · ✓ Masa menunggu dikurangkan"],
5:["Kad tajuk “5 · e-Invois” atas foto peniaga kedai","Tajuk “Ambang pengecualian e-Invois”","RM1 JUTA ›› RM3 JUTA (jualan tahunan)","Kad “≤ RM3 juta tidak diwajibkan e-Invois” + kad kuning ✓ meringankan beban pematuhan PMKS","Foto bertukar ke peniaga wanita; ikon graf naik “Lebih tumpuan kepada pertumbuhan perniagaan”"],
6:["Kad tajuk “6 · Bantuan Penjaja & Peniaga Kecil” atas foto penjaja","Kad Geran Sejahtera MADANI → RM200 JUTA","✓ Penjaja · ✓ Peniaga kecil · ✓ Peniaga pasar malam · ✓ Ibu bekerja dari rumah","Pembiayaan Mikro: + RM1 BILION; RM5 BILION ›› RM6 BILION (pada 2026)"],
7:["Latar skyline KL, carta bar naik + anak panah; ✓ Perniagaan kecil terus berkembang, ✓ Pendapatan rakyat terus meningkat"]}
secs={}
for i,(s,t,x) in enumerate(items):
    t1=items[i+1][1] if i+1<len(items) else END
    secs.setdefault(s,[]).append((t+OFF,t1+OFF,x))
cuts=json.load(open(sys.argv[3]))["cuts"]
manual=[(43.92,44.53,"Tersasul “pe–” sebelum “penyelenggaraan”"),(78.92,82.30,"Ambilan pertama “disasarkan menerima peluang pembelajaran…” — ambil semula (retake) dikekalkan"),(135.28,136.24,"Tersasul “Bagi me–” — ambil semula dikekalkan"),(176.56,177.24,"Tersasul “Pembiar–” — ambil semula dikekalkan")]
def hl(x):
    return re.sub(r'(RM[\d.]+(?: (?:bilion|juta))?|\b\d[\d.,%]*(?: (?:liter|juta|ribu|bulan|tahun))?)',r'<b class="num">\1</b>',html.escape(x))
rows=""
md=["# Skrip Video Komuniti MADANI — *Enam Ikhtiar Untuk Rakyat*","",f"**Durasi akhir:** {mm(OFF+END+4.5)} (intro 4s + VO {mm(END)} + end card 4.5s)  ","**Format:** 16:9 · 1920×1080 · 30fps (preview: 640×360 · 15fps)  ","**Suara latar:** dibersihkan (noise reduction, EQ, kompresor, −16 LUFS)","",
    "| Babak | Masa | Skrip VO | Visual / Motion Grafik |","|---|---|---|---|"]
rows+=f'<tr class="sec"><td colspan="3"><span class="badge">INTRO</span> Pembukaan</td></tr><tr><td class="tm">0:00.0 – 0:04.0</td><td class="vo"><i>(Tiada VO)</i></td><td class="vis"><ul><li>Skyline KL, logo Malaysia MADANI</li><li>Bar kuning “ENAM IKHTIAR UNTUK RAKYAT” (slam)</li><li>6 ikon ikhtiar muncul berturut-turut</li></ul></td></tr>'
md.append("| Intro | 0:00.0 – 0:04.0 | *(Tiada VO)* | Skyline KL, logo, bar “ENAM IKHTIAR UNTUK RAKYAT”, 6 ikon |")
for s in sorted(secs):
    n,title=SEC[s]; L=secs[s]
    badge="PENUTUP" if s==7 else f"IKHTIAR {n}"
    rows+=f'<tr class="sec"><td colspan="3"><span class="badge">{badge}</span> {html.escape(title)} <span class="rng">{mm(L[0][0])} – {mm(L[-1][1])}</span></td></tr>'
    vis=VIS[s]
    for j,(a,b,x) in enumerate(L):
        assert len(vis)==len(L),(s,len(vis),len(L))
        v=f"<li>{html.escape(vis[j])}</li>"
        rows+=f'<tr><td class="tm">{mm(a)} – {mm(b)}</td><td class="vo">{hl(x)}</td><td class="vis"><ul>{v}</ul></td></tr>'
        md.append(f"| {badge if j==0 else ''} | {mm(a)} – {mm(b)} | {x} | {vis[j]} |")
O=OFF+END
rows+=f'<tr class="sec"><td colspan="3"><span class="badge">END CARD</span> {mm(O)} – {mm(O+4.5)}</td></tr><tr><td class="tm">{mm(O)} – {mm(O+4.5)}</td><td class="vo"><i>(Tiada VO)</i></td><td class="vis"><ul><li>Logo + “ENAM IKHTIAR UNTUK RAKYAT” + 6 tile ringkasan</li></ul></td></tr>'
md.append(f"| End card | {mm(O)} – {mm(O+4.5)} | *(Tiada VO)* | Logo + 6 tile ringkasan |")
edits="".join(f"<li><b>{a:.2f}s – {b:.2f}s</b> (audio asal): {html.escape(w)}</li>" for a,b,w in manual)
md+=["","## Suntingan suara latar","","**Ulangan / tersasul dibuang:**",""]+[f"- {a:.2f}s – {b:.2f}s (audio asal): {w}" for a,b,w in manual]+["",f"**Jeda janggal dipendekkan:** {len(cuts)-len(manual)} tempat — jeda dalam ayat ≤ 0.26s, antara ayat ≈ 0.42s, antara ikhtiar ≈ 0.85s. Senyap awal 2.8s dan akhir 4.7s dibuang.","","**Jumlah:** 3:18.2 → 2:52.1 (−26.0s)","",
 "**Pemprosesan audio:** noise reduction spektral (noisereduce), high-pass 75 Hz, potong 220 Hz −2.5 dB (kurangkan bunyi ‘berdengung’), tambah kejelasan 3.2 kHz +2.5 dB & 10.5 kHz +1.5 dB, de-esser, kompresor 3:1, limiter, loudness −16 LUFS / −1.5 dBTP.","",
 "## Nota untuk semakan","","- VO menyebut **“pada tahun 2027”** untuk peruntukan sekolah — tiada dalam storyboard. Disertakan pada skrin sebagai “Tahun 2027”.","- Storyboard ada **“Berkuat kuasa 1 September 2026”** (BUDI MADANI) tetapi VO tidak menyebutnya — dikekalkan sebagai teks atas skrin sahaja.","- VO menyebut “capaian internet” dalam Ikhtiar 4 — ditambah ikon Wi-Fi.","- Ejaan sari kata telah dibetulkan (cth. “kesihatan”, “meringankan”, “penyempurnaan”, “menikmati”, “Geran Sejahtera MADANI”).","- Foto dalam preview diambil daripada imej storyboard (resolusi rendah). Untuk versi akhir, gantikan dengan footage/B-roll atau foto resolusi tinggi.","- Tiada muzik latar dibekalkan — boleh ditambah pada versi akhir."]
open(f"{outdir}/SKRIP_VO.md","w").write("\n".join(md)+"\n")
page=f'''<!doctype html><html lang="ms"><head><meta charset="utf-8"><title>Skrip Enam Ikhtiar</title><link rel="stylesheet" href="../build/fonts/fonts.css">
<style>@page{{size:A4 landscape;margin:12mm}}*{{box-sizing:border-box}}body{{font-family:Montserrat,Inter,sans-serif;color:#0a2563;margin:0;font-size:10.5pt}}
.hero{{background:linear-gradient(120deg,#0a2563,#1d6fe8);color:#fff;border-radius:14px;padding:18px 24px;display:flex;justify-content:space-between;align-items:center}}
.hero h1{{margin:4px 0 0;font-size:24pt;font-weight:900;font-style:italic}} .hero .k{{color:#ffcb1f;font-weight:800;letter-spacing:2px;font-size:9pt}}
.meta{{display:grid;grid-template-columns:repeat(2,auto);gap:4px 16px;font-size:9pt;text-align:right}} .meta b{{color:#ffcb1f}}
table{{width:100%;border-collapse:separate;border-spacing:0;margin-top:14px}} th{{text-align:left;font-size:8.5pt;letter-spacing:1px;color:#5b6b8f;padding:6px 10px;border-bottom:2px solid #0a2563}}
td{{padding:8px 10px;vertical-align:top;border-bottom:1px solid #e3e9f5}} tr{{break-inside:avoid}}
tr.sec td{{background:#eef4ff;font-weight:900;font-size:12pt;padding:9px 10px;border-bottom:none;border-top:10px solid #fff}}
.badge{{background:#e3252f;color:#fff;font-style:italic;border-radius:6px;padding:2px 9px;margin-right:8px;font-size:9.5pt}} .rng{{float:right;font-weight:700;color:#5b6b8f;font-size:9pt}}
.tm{{width:120px;font-weight:700;color:#1d6fe8;white-space:nowrap;font-size:9pt}} .vo{{width:46%;font-size:11pt;line-height:1.5;font-weight:500}} .vis ul{{margin:0;padding-left:16px;font-size:9pt;color:#33466f}}
.num{{background:#ffcb1f;padding:0 4px;border-radius:4px;font-weight:800}}
h2{{font-size:13pt;margin:18px 0 6px;font-weight:900}} .cols{{display:grid;grid-template-columns:1fr 1fr;gap:18px;break-inside:avoid}} .box{{background:#f5f8ff;border-radius:12px;padding:12px 16px;font-size:9.5pt;line-height:1.5}} .box ul{{margin:4px 0;padding-left:18px}}
</style></head><body>
<div class="hero"><div><div class="k">SKRIP SUARA LATAR &amp; MOTION GRAFIK</div><h1>Video Komuniti MADANI — Enam Ikhtiar Untuk Rakyat</h1></div>
<div class="meta"><span>Durasi</span><b>{mm(OFF+END+4.5)}</b><span>VO (selepas suntingan)</span><b>{mm(END)}</b><span>Format</span><b>16:9 · 1080p</b></div></div>
<table><thead><tr><th>MASA</th><th>SKRIP SUARA LATAR</th><th>VISUAL / MOTION GRAFIK</th></tr></thead><tbody>{rows}</tbody></table>
<div class="cols"><div class="box"><h2>Suntingan suara latar</h2><b>Ulangan / tersasul dibuang:</b><ul>{edits}</ul>
<b>Jeda janggal dipendekkan:</b> {len(cuts)-len(manual)} tempat (dalam ayat ≤ 0.26s, antara ayat ≈ 0.42s, antara ikhtiar ≈ 0.85s). Senyap awal &amp; akhir dibuang.<br><b>Jumlah:</b> 3:18.2 → 2:52.1 (−26.0s)<br>
<b>Audio:</b> noise reduction, high-pass 75 Hz, EQ (−2.5 dB @220 Hz, +2.5 dB @3.2 kHz, +1.5 dB @10.5 kHz), de-esser, kompresor 3:1, −16 LUFS.</div>
<div class="box"><h2>Nota untuk semakan</h2><ul><li>VO sebut <b>“pada tahun 2027”</b> (sekolah) — tiada dalam storyboard; dipaparkan sebagai “Tahun 2027”.</li><li><b>“Berkuat kuasa 1 September 2026”</b> ada dalam storyboard tetapi tidak disebut VO — dikekalkan sebagai teks skrin.</li><li>“Capaian internet” (Ikhtiar 4) — ditambah ikon Wi-Fi.</li><li>Ejaan sari kata dibetulkan daripada sebutan VO.</li><li>Foto preview dipotong daripada storyboard (resolusi rendah) — gantikan dengan B-roll/foto HD untuk versi akhir.</li><li>Muzik latar belum ditambah.</li></ul></div></div>
</body></html>'''
open(f"{outdir}/skrip.html","w").write(page)
