#!/usr/bin/env bash
set -euo pipefail

# make_video.py の最小動作確認用に、3秒の通常動画を生成します。
python3 scripts/make_video.py \
  --output export/update.mp4 \
  --title "Codex CLI 動画生成テスト" \
  --message "ローカルで生成した短いサンプル動画です。" \
  --duration 3 \
  "$@"
