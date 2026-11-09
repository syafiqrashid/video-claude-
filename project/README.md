# Enam Ikhtiar Untuk Rakyat — Motion Graphic

- `output/enam_ikhtiar_480p.mp4` — video akhir (854×480, 25fps, ±3:42)
- `output/vo_bersih.m4a` — voice over selepas potong + bersihkan
- `SKRIP.md` — skrip VO mengikut babak dengan timestamp baharu

## Pipeline
1. `transcribe.py` — faster-whisper (medium, bahasa Melayu) dengan timestamp perkataan.
2. `edit_audio.py` — noisereduce, VAD, mampatkan pause, buang tersasul/ulangan (`manual_cut`), hasilkan `map.json` (masa asal → masa baharu).
   Kemudian ffmpeg: highpass, EQ, compressor, loudnorm −16 LUFS.
3. `motion.html` — semua grafik dilukis dengan canvas, ikut storyboard 8 babak; kotak "Cadangan Motion" diganti panel **SKRIP VO** (karaoke ikut suara).
4. `render.js` — Playwright render bingkai demi bingkai → ffmpeg (x264 CRF 28, AAC 96k).

```
node render.js map.json script.json output/enam_ikhtiar_480p.mp4 vo_final.wav
```
