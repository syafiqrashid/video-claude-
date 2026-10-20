# Belanjawan Madani 2027 — edit notes

Sources (Google Drive): `A` = main take (4:43, 4K HEVC portrait), `B` = outro (0:32).
`assets/A.mp4` / `assets/B.mp4` are 1080x1920 30fps H.264 proxies with loudness-normalised audio
(-16 LUFS). They are git-ignored (180 MB); regenerate from the originals:

```bash
ffmpeg -i <original> -map 0:v:0 -map 0:a:0 -vf "scale=1080:1920,fps=30" -c:v libx264 -crf 20 \
  -af "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -b:a 192k -movflags +faststart assets/A.mp4
```

Rebuild `index.html` after editing `build/edl.json`, `build/build.py` or `build/template.html`:
`python3 -I build/build.py && npx hyperframes check`

## Cut list (source seconds → timeline) — 5:16 combined → 2:50

| # | Source | Kept | Why |
|---|--------|------|-----|
| Hook | A 3.5–11.2 | "Tahukah anda apakah manfaat Belanjawan 2027…untuk kita dan keluarga?" | Question moved before the salam; number teaser (RM200 / RM870 JUTA / RM16 BILION / 30%) flashes over it |
| Salam | A 0.8–3.5 | "Assalamualaikum dan salam Malaysia Madani." | |
| Intro | A 11.3–19.7 | "…jom kita lihat 6 inisiatif…" | |
| 1 | A 21.9–33.3 | BAP RM150 → RM200 | Pause before "Bantuan" trimmed |
| 2 | A 40.5–60.6 | RMT RM870 juta | Removed 33–40s (turned away from camera) |
| 3 | A 155.5–174.7 | Tingkatan 6 RM2,500 | **Removed 60–155s**: four failed takes ("Alamak", "Aduh habis saya", drinking break) |
| 4 | A 182.3–205.3 | STR & SARA RM16 bilion | Removed 175–182s dead air, trimmed pause after "Keempat" |
| 5 | A 229.7–253.3 | SARA Madani RM100 × 2 | **Removed first take 207–229s** (flubbed "syarat pelangsanakan"); second take is complete |
| 6 | A 255.4–282.4 | Jualan Rahmah & Agro Madani | |
| Outro | B 0–31.8 | Recap, closing, CTA | |

## Graphics & sound
- Kinetic captions (Montserrat 900, karaoke word light-up, numbers in gold), transcript hand-corrected.
- Section badge 01–06 + 6-step progress bar, gold sweep between sections.
- Number callout cards with camera punch-in on every key figure; chip pop-ins for ayam/ikan/sayur/buah.
- Outro: 6-item recap list, "Menggapai di langit, mengakar di bumi" title, Malaysia MADANI card, LIKE/SHARE CTA.
- Alternating 1.0×/1.14× framing on same-take cuts to hide jump cuts.
- SFX (bundled HyperFrames library, see `assets/sfx/CREDITS.md`): whoosh on sections, ping/pop on numbers, bass impact on hook and RM16 bilion / 30%, click on recap, sparkle on quote, chime on CTA.
- No background music yet.
