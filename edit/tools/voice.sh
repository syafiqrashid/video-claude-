#!/usr/bin/env bash
# Clean the speaker's voice and swap it into a footage proxy (video stream copied).
# usage: tools/voice.sh <original iPhone .mp4> <proxy .mp4 to update>
# needs: pip install deepfilternet ; DF_MODEL=<dir of unzipped DeepFilterNet3 model>
set -euo pipefail
src=$1; proxy=$2; tmp=$(mktemp -d)
ffmpeg -y -v error -i "$src" -map 0:a:0 -ac 1 -ar 48000 "$tmp/raw.wav"
python3 -I "$(dirname "$0")/dfn.py" "$tmp/raw.wav" "$tmp/df.wav"          # AI noise removal
# clarity: cut rumble + mud, lift consonants (3.2k) + air, gentle compression, -15 LUFS
EQ="highpass=f=90,equalizer=f=220:t=q:w=1.0:g=-4,equalizer=f=3200:t=q:w=0.9:g=6,highshelf=f=6500:g=3,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,loudnorm=I=-15:TP=-1.5:LRA=7"
ffmpeg -y -v error -i "$tmp/df.wav" -af "$EQ" -ar 48000 -ac 2 "$tmp/voice.wav"
ffmpeg -y -v error -i "$proxy" -i "$tmp/voice.wav" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$tmp/out.mp4"
mv -f "$tmp/out.mp4" "$proxy"; rm -rf "$tmp"
