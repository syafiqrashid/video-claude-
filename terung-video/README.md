# Video: Daun Lebat, Buah Sikit? (Terung)

Video 30 saat, menegak 9:16 (1080×1920, 30 fps), untuk Reels/TikTok, ikut storyboard 6 babak.

| Babak | Masa | Kandungan |
|---|---|---|
| 1 | 0:00–0:04 | Hook: "Daun Lebat, Buah Sikit?" (zoom in) |
| 2 | 0:04–0:09 | Punca Utama: daun & batang terlalu dominan (pop up) |
| 3 | 0:09–0:16 | Nutrien perlu seimbang: N berlebihan lawan NPK seimbang (carta bar) |
| 4 | 0:16–0:22 | Faktor lain: cahaya, suhu, pendebungaan (slide in) |
| 5 | 0:22–0:27 | Jangan tengok daun sahaja: senarai semak + kanta pembesar |
| 6 | 0:27–0:30 | Kesimpulan + "Lebih Banyak Buah, Lebih Menguntungkan!" |

Output: `terung-daun-lebat-buah-sikit.mp4`

## Jana semula
```bash
python3 music.py music.wav           # muzik latar + bunyi whoosh
node render.js frames                # render 900 frame dari index.html (Playwright)
ffmpeg -framerate 30 -i frames/f%04d.jpg -i music.wav -c:v libx264 -crf 20 \
  -pix_fmt yuv420p -c:a aac -shortest terung-daun-lebat-buah-sikit.mp4
```
Edit teks/masa dalam `index.html` (setiap babak ialah satu panggilan `S(mula, tamat, html)`).
