#!/bin/bash
# Robust, self-resuming download of the large-v3 model.bin.
# Patiently waits for connectivity during a network outage instead of burning
# retries. Optional -- faster-whisper downloads the model automatically on first
# run; use this only on flaky connections. Run from Git Bash on Windows.
DIR="$(cd "$(dirname "$0")" && pwd)"
F="$DIR/models/large-v3/model.bin"
URL="https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main/model.bin"
TARGET=3087284237
LOG="$DIR/models/dl.log"

mkdir -p "$DIR/models/large-v3"
echo "=== download loop (v2) started ===" >> "$LOG"
for i in $(seq 1 1000); do
  sz=$(stat -c %s "$F" 2>/dev/null || echo 0)
  if [ "$sz" -ge "$TARGET" ]; then
    echo "DONE after round $i: $sz bytes" | tee -a "$LOG"
    exit 0
  fi
  # wait for internet (up to 10 min) before trying curl
  for w in $(seq 1 60); do
    if curl -sI --max-time 10 https://huggingface.co >/dev/null 2>&1; then break; fi
    echo "round $i: no network, waiting 10s ($w/60)" >> "$LOG"
    sleep 10
  done
  echo "round $i: $sz / $TARGET bytes -> curl (resume)" >> "$LOG"
  curl -L --fail --retry 10 --retry-delay 5 -C - -o "$F" "$URL" >> "$LOG" 2>&1
  sleep 2
done
echo "loop limit reached at $(stat -c %s "$F" 2>/dev/null) bytes" | tee -a "$LOG"
exit 1
