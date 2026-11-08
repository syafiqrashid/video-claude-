# Video Komuniti MADANI — Enam Ikhtiar Untuk Rakyat

Video motion grafik ikut storyboard, dengan suara latar yang dah disunting dan dibersihkan.

## Fail utama
| Fail | Keterangan |
|---|---|
| `output/preview_360p.mp4` | **Preview resolusi rendah** (640×360, 15fps, 3:00.7) — visual + VO + sari kata |
| `output/vo_bersih.m4a` | Suara latar akhir (dah disunting, noise reduction, EQ, −16 LUFS) |
| `output/AB_sebelum_selepas.m4a` | Perbandingan: ~22s audio asal → senyap 1.2s → bahagian sama selepas dibersihkan |
| `skrip/SKRIP_VO.pdf` | Skrip lengkap (masa, VO, visual setiap babak) + senarai suntingan + nota semakan |
| `skrip/SKRIP_VO.md` | Skrip yang sama dalam Markdown |

## Suntingan suara latar
- **4 ulangan/tersasul dibuang**: "pe–penyelenggaraan", ambilan pertama "disasarkan menerima peluang pembelajaran…" (retake dikekalkan), "Bagi me–", "Pembiar–".
- **33 jeda janggal dipendekkan** (dalam ayat ≤0.26s, antara ayat ≈0.42s, antara ikhtiar ≈0.85s), senyap di awal dan hujung dibuang.
- 3:18.2 → 2:52.1.

## Render semula (contoh 1080p 30fps)
```bash
# perlukan: ffmpeg, node + playwright, python3 (faster-whisper, noisereduce, soundfile)
node tools/render.js motion output/final_1080p.mp4 <vo_final.wav> 1920 30
```
- `motion/index.html` — motion grafik (HTML/CSS/JS, `render(t)` deterministik). Masa setiap elemen ikut masa perkataan dalam VO.
- `motion/script_data.js` — teks skrip + masa ayat. `tools/make_captions.py` hasilkan `captions.js`.
- Tambah `#nocap` pada URL kalau tak mahu sari kata.
- `tools/edit_audio.py` (potong jeda + retake), `tools/enhance.py` + rantai ffmpeg (dalam sejarah commit) untuk pembersihan.
