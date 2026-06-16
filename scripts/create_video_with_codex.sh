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
case "${OUTPUT_PATH}" in
  /*) OUTPUT_FILE="${OUTPUT_PATH}" ;;
  *) OUTPUT_FILE="${REPO_ROOT}/${OUTPUT_PATH}" ;;
esac

codex exec --cd "${REPO_ROOT}" --sandbox workspace-write "このリポジトリで、ChatGPT / Codex の判断だけで短い MP4 動画を作成してください。scripts/make_video.py、scripts/create_sample_video.sh、scripts/create_sample_video.bat は使用しないでください。ffmpeg など利用可能なコマンドを自分で選び、出力先 ${OUTPUT_PATH} に動画ファイルを直接作成してください。タイトルは「${TITLE}」、メッセージは「${MESSAGE}」、長さは ${DURATION} 秒です。output ディレクトリが無ければ作成してください。動画生成に必要なコマンド実行以外の repository ファイル編集はしないでください。最後に ${OUTPUT_PATH} が存在し、空ファイルではないことを確認してください。"

if [ ! -s "${OUTPUT_FILE}" ]; then
  echo "Codex CLI did not create a video file: ${OUTPUT_PATH}" >&2
  exit 1
fi

echo "Codex CLI created video: ${OUTPUT_PATH}"
