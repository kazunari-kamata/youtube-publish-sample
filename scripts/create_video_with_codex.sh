#!/usr/bin/env bash
set -euo pipefail

if ! command -v codex >/dev/null 2>&1; then
  echo "codex command was not found. Install and sign in to Codex CLI first." >&2
  exit 1
fi

OUTPUT_PATH="${CODEX_VIDEO_OUTPUT:-output/update.mp4}"
TITLE="${CODEX_VIDEO_TITLE:-Codex CLI 動画生成テスト}"
MESSAGE="${CODEX_VIDEO_MESSAGE:-ChatGPT / Codex CLI から生成した短いサンプル動画です。}"
DURATION="${CODEX_VIDEO_DURATION:-3}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

codex exec --cd "${REPO_ROOT}" --sandbox workspace-write "このリポジトリで、既存の scripts/make_video.py を使って短い MP4 動画を作成してください。出力先は ${OUTPUT_PATH}、タイトルは「${TITLE}」、メッセージは「${MESSAGE}」、長さは ${DURATION} 秒です。output ディレクトリが無ければ作成してください。動画生成以外のファイル編集はしないでください。"
