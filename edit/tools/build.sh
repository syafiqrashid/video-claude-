#!/usr/bin/env bash
# Rebuild index.html, then re-apply the voiceover carve on the music bed.
# CORE: a dir containing node_modules/@hyperframes/core (npm i @hyperframes/core@0.8.162)
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -I tools/edl.py tools/transcripts >/dev/null
python3 -I tools/build.py
node "${CARVE:-$HOME/.claude/skills/hyperframes-audio/scripts/carve.mjs}" --comp index.html --bed music-bed --strength 0.7 ${CORE:+--core "$CORE"} | tail -3
