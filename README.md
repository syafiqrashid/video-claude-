# Video Merdeka — Warisan Perjuangan

Video menegak 1080x1920 (39.6s) dibina dengan [HyperFrames](https://hyperframes.heygen.com) mengikut storyboard 4 frame.

- `output/merdeka-warisan-perjuangan-lowres.mp4` — preview low res (540x960)
- `merdeka/index.html` — komposisi HyperFrames (semua animasi GSAP)
- `assets/voice-raw.m4a` — rakaman suara asal; `assets/storyboard-v2.png` — storyboard terkini (v1: `assets/storyboard.png`, untuk foto kad)
- `scripts/cut_voice.py` — buang pause janggal (56.5s → 38.5s), normalize suara → `merdeka/assets/voice.wav`
- `scripts/extract_art.py` — potong ilustrasi dari storyboard → `merdeka/assets/art/`

Render semula: `cd merdeka && npx hyperframes render -o ../output/merdeka-warisan-perjuangan.mp4`
(jalankan skrip dari root repo: `python3 scripts/cut_voice.py`; `cd merdeka && python3 ../scripts/extract_art.py`)
