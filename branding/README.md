# Kupas Daily — Logo

**Konsep:** "Kupas" = mengupas. Ikon ialah helaian/kad dengan bucu atas kanan yang
terkupas (lipatan amber), mendedahkan lapisan di bawah — simbol mengupas isu
hingga ke dasar. Huruf **k** dibina dengan sudut 45° yang selari dengan garis
lipatan, jadi ikon nampak satu sistem.

| Fail | Guna untuk |
|---|---|
| `kupas-daily-horizontal.svg` | Logo utama (latar cerah) — header, thumbnail, dokumen |
| `kupas-daily-horizontal-dark.svg` | Logo utama atas latar gelap |
| `kupas-daily-stacked.svg` / `-dark.svg` | Versi tegak — poster, intro/outro video, slide |
| `kupas-daily-icon.svg` | Ikon sahaja (favicon, watermark video) |
| `kupas-daily-avatar.svg` | Gambar profil (YouTube, TikTok, IG, FB) |

PNG (2x) ada dalam `png/`. Semua teks sudah ditukar ke *path*, jadi SVG
dipaparkan sama di mana-mana tanpa perlu font.

## Warna

| Nama | Hex |
|---|---|
| Navy (utama) | `#0B1F3A` |
| Amber (aksen) | `#F5A524` |
| Slate (teks sekunder) | `#5B6B84` |
| Putih | `#FFFFFF` |

**Font:** Inter Display ExtraBold (KUPAS), Inter SemiBold dengan jarak huruf
lebar (DAILY).

## Jana semula

```
pip install fonttools
python3 branding/build.py
```
