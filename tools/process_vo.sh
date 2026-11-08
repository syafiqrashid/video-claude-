#!/usr/bin/env bash
# Full VO pipeline: input m4a -> edited + cleaned vo_final.wav
# usage: tools/process_vo.sh input/vo_asal.m4a workdir
set -euo pipefail
IN=$1; W=$2; T=$(cd "$(dirname "$0")" && pwd); mkdir -p "$W"; cd "$W"
ffmpeg -loglevel error -y -i "$IN" -ac 1 -ar 48000 vo48k.wav
ffmpeg -loglevel error -y -i "$IN" -ac 1 -ar 16000 vo16k.wav
python3 -I "$T/transcribe.py" vo16k.wav medium trans.json
ffmpeg -hide_banner -i vo48k.wav -af silencedetect=noise=-40dB:d=0.25 -f null - 2>&1 | grep -oE "silence_(start|end): [0-9.]+" | awk '{print $2}' | paste - - > sil.txt
python3 -I "$T/edit_audio.py" vo48k.wav sil.txt trans.json vo_edit.wav cutmap.json
python3 -I "$T/enhance.py" vo_edit.wav vo_nr.wav
CH="highpass=f=75:poles=2,equalizer=f=220:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,equalizer=f=10500:t=q:w=1.5:g=1.5,deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=-21dB:ratio=3:attack=8:release=120:makeup=2,alimiter=limit=0.95:level=false"
J=$(ffmpeg -hide_banner -i vo_nr.wav -af "$CH,loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
MI=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -loglevel error -y -i vo_nr.wav -af "$CH,loudnorm=I=-16:TP=-1.5:LRA=7:$MI:linear=true,aresample=48000" -c:a pcm_s24le vo_final.wav
echo "done: $W/vo_final.wav"
