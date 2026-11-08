# Video Merdeka — Warisan Perjuangan

Video menegak 1080x1920 (39.6s) dibina dengan [HyperFrames](https://hyperframes.heygen.com) mengikut storyboard 4 frame.

- `output/merdeka-warisan-perjuangan-HD.mp4` — video siap HD (1080x1920)
- `output/merdeka-warisan-perjuangan-lowres.mp4` — preview low res (540x960)
- `merdeka/index.html` — komposisi HyperFrames (semua animasi GSAP)
- `assets/voice-raw.m4a` — rakaman suara asal; `assets/storyboard-v3.png` — storyboard terkini (gambar pemimpin); v2 untuk ilustrasi sketsa
- `scripts/cut_voice.py` — buang pause janggal (56.5s → 38.5s), normalize suara → `merdeka/assets/voice.wav`
- `scripts/extract_art.py` — potong ilustrasi dari storyboard → `merdeka/assets/art/`

Render semula: `cd merdeka && npx hyperframes render -o ../output/merdeka-warisan-perjuangan.mp4`
(jalankan skrip dari root repo: `python3 scripts/cut_voice.py`; `cd merdeka && python3 ../scripts/extract_art.py`)

## Video 2 — Manfaat Merdeka

Video menegak 1080x1920 (28.6s) dalam `video2/`, gaya animasi sama dengan video pertama.

- `video2/output/manfaat-merdeka-HD.mp4` — video siap HD (1080x1920)
- `video2/output/manfaat-merdeka-lowres.mp4` — preview low res (540x960)
- `video2/index.html` — komposisi HyperFrames
- `video2/raw/` — rakaman asal, storyboard, transkrip (`words.json`) dan peta potongan
- `scripts/cut_voice2.py` — buang pause janggal + take berulang "daripada kemudahan pendidikan" (49.2s → 27.4s)
- `scripts/extract_art2.py` — potong foto dan ilustrasi dari storyboard

Render: `cd video2 && npx hyperframes render -o output/manfaat-merdeka-HD.mp4`

## Video 3 — Patriotisme

Video menegak 1080x1920 (35.6s) dalam `video3/`, ikut storyboard patriotisme (`video3/raw/storyboard.png`).

- `video3/output/patriotisme-HD.mp4` — video siap HD (1080x1920)
- `video3/output/patriotisme-lowres.mp4` — preview low res (540x960)
- `video3/index.html` — komposisi HyperFrames
- `scripts/cut_voice3.py` — buang pause janggal (52.4s → 34.5s); tiada skrip berulang dalam rakaman ini
- `scripts/extract_art3.py` — potong foto dari storyboard

## Video 4 — Kesejahteraan

Video menegak 1080x1920 (47.4s) dalam `video4/`, ikut storyboard `video4/raw/storyboard.png`.

- `video4/output/kesejahteraan-HD.mp4` — video siap HD (1080x1920)
- `video4/output/kesejahteraan-lowres.mp4` — preview low res (540x960)
- `video4/index.html` — komposisi HyperFrames
- `scripts/cut_voice4.py` — buang pause janggal dari rakaman semula `voice-raw-v2.m4a` (65.7s → 46.4s); rakaman lama `voice-raw.m4a` tak ada suara frame 4
- `scripts/extract_art4.py` — potong foto, ilustrasi dan logo dari storyboard

## Video penuh — 4 bahagian

- `final/merdeka-4-bahagian-HD.mp4` — keempat-empat video digabung (1080x1920, 2:31)
- `final/merdeka-4-bahagian-lowres.mp4` — preview low res
- `scripts/enhance_and_join.py` — susun ikut skrip (Manfaat Merdeka → Warisan Perjuangan → Patriotisme → Kesejahteraan), bersihkan suara (noise reduction, EQ, de-esser, compressor, -14 LUFS) dan gabung

## Video 5 — Jiwa Merdeka (talking head)

Dua klip (IMG_2863 + IMG_2864) digabung, take berulang dan pause janggal dibuang, latar bilik diganti studio, suara dibersihkan, animasi ringkas ikut video reference.

- `video5/output/jiwa-merdeka-HD.mp4` — video siap HD (1080x1920, 51.6s, -14 LUFS)
- `video5/output/jiwa-merdeka-lowres.mp4` — preview low res (540x960)
- `video5/index.html` — komposisi HyperFrames (overlay, caption ikut suara, end card)
- `video5/studio/studio.html` — latar studio
- `scripts/v5_cut.py` → `v5_matte.py` (RVM) → `v5_composite.py` → `v5_audio.py`
- Rakaman asal & fail perantaraan tak masuk repo (`video5/raw`, `video5/work`)

## Video penuh — Opening + 4 point + Closing

- `final/merdeka-penuh-HD.mp4` — 1080x1920, 3:23 (opening Jiwa Merdeka → Manfaat Merdeka → Warisan Perjuangan → Patriotisme → Kesejahteraan → closing + end card)
- `final/merdeka-penuh-lowres.mp4` — preview low res
- `scripts/enhance_and_join_full.py` — bersihkan suara 4 point, potong opening/closing dari video 5, gabung
