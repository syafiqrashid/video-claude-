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
