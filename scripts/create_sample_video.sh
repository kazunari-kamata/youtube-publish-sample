#!/usr/bin/env bash
set -euo pipefail

python3 scripts/make_video.py \
  --output export/update.mp4 \
  --title "Codex CLI 動画生成テスト" \
  --message "ローカルで生成した短いサンプル動画です。" \
  --duration 3 \
  "$@"
