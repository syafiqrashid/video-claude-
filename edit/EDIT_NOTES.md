# Nota Edit — Perlindungan Bil Elektrik 800 kWh

**Sumber:** Video 1 (3:06) + Video 2 (0:42) → **Edit: 2:11** (1080×1920, 30fps)

## Struktur
| Masa edit | Sumber | Isi | Grafik / SFX |
|---|---|---|---|
| 0:00–0:03.7 | V1 7.3s | **HOOK** "Korang, bila bil api korang naik mendadak bulan ni…" | Slam title *BIL ELEKTRIK NAIK MENDADAK?* + bass impact + shake |
| 0:03.7–0:19 | V1 11.7s | "Jangan stres… berita baik… Kerajaan MADANI… Sept–31 Dis 2026" | *JANGAN STRES!* · *ADA BERITA BAIK!* · kad Madani · kad tarikh |
| 0:19–0:28 | V1 28s | "600 kWh kepada 800 kWh sebulan. Ok, kenapa?" | Meter 600→800 kaunter + impact · *KENAPA?* |
| 0:28–0:42.6 | V1 38.7s | Cuaca panas, jerebu, kipas & aircon, ruang tambahan 800 | Chip panas/jerebu · kipas berpusing · *800 kWh* |
| 0:42.6–0:49.5 | V1 57.9s | **JOLOK MANGGA (penuh, tak dipotong)** | Sticker *JAP… JOLOK MANGGA DULU* + mangga jatuh |
| 0:49.5–1:17 | V1 64.8s | "Apa korang dapat?… 3 caj: AFA, peruncitan, SST… lebih ramai dilindungi" | Senarai 3 caj dengan tick satu-satu ikut sebutan |
| 1:17–1:28.7 | V1 98s / 115.5s / 125s | **SAPU SAMPAH (semua 3 shot sapu dikekalkan, laju 1.5x)** | Tag *SAMBIL SAPU SAMPAH…* · *PESANAN PENTING* |
| 1:28.7–1:42.4 | V1 131.3s | "Sekarang saya nak pesan… guna berhemah… jimat elektrik, jimat duit" | Kad had 800 · *GUNA ELEKTRIK SECARA BERHEMAH* · *JIMAT ELEKTRIK = JIMAT DUIT* |
| 1:42.4–1:43.4 | V1 154.5s | "Kesimpulannya" | Band *KESIMPULANNYA* |
| 1:43.4–2:11 | **V2** 13s | Kesimpulan penuh + "Share video ini…" | Pantau · seimbang · recap 600→800 · Ikhtiar MADANI · CTA *SHARE* |

## Yang dibuang
- **V1 0–7s** — b-roll pokok + jalan masuk frame (hook terus ke ayat pertama).
- **Jeda janggal** — 0.7s+ senyap dalam ayat (cth. "jangan … stres", "perlindungan … bil", sebelum "caj AFA").
- **V1 55.6–57.9s** — berdiri senyap sebelum jolok mangga (bukan aksi mangga).
- **V1 106–115.5s, 119.1–125s** — take tersilap: "Walaupun… Sekarang… Alamak" + jalan ke kamera. Shot sapu sampah di antaranya **dikekalkan**.
- **V1 145–154s** — "Ok, betul… terima kasih" (outtake).
- **V1 155.5–186s** — kesimpulan V1 (berulang) → guna take V2 yang lebih bersih.
- **V2 0–13s** — kamera tengah set ("Apa lah, terbalik pula. Tengah-tengah").

## Teknikal
- Audio suara: noise reduction ringan + loudness −15 LUFS.
- Footage iPhone HDR (HLG) → tone-map ke SDR BT.709 supaya warna betul di semua platform.
- Caption karaoke (perkataan aktif kuning). Transkripsi dibetulkan: "Ahmadiyah"→MADANI, "hak"→had, dll.
- Punch-in zoom pada jump cut untuk sembunyikan potongan.
- SFX: whoosh, pop, impact, ping, chime, notification (Pixabay license).
- **Muzik latar (pilihan A, santai):** akustik/ukulele ~79 BPM, dijana sendiri dengan MusicGen (bebas lesen), di-loop ikut bar (8 bar) supaya rentak tak tersadung. Fail: `assets/music/bed.mp3`.
  - Voiceover carve: muzik beri ruang pada frekuensi suara (160–630 Hz) dan turun bila bercakap; naik sedikit masa jolok mangga & sapu sampah. Fade in/out di awal & hujung.

## Fail
- `index.html` — dijana oleh `tools/build.py` (grafik/SFX/caption) daripada `tools/edl.json` (`tools/edl.py` = senarai potongan).
- Ubah potongan → edit `SEGS` dalam `tools/edl.py`, kemudian run `tools/build.sh` (bina semula + carve muzik; perlukan `@hyperframes/core`, set `CORE=<dir>`).
