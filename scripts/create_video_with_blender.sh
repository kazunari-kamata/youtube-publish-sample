#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BLENDER_BIN="${BLENDER_BIN:-}"

if [ -z "${BLENDER_BIN}" ]; then
  if command -v blender >/dev/null 2>&1; then
    BLENDER_BIN="$(command -v blender)"
  elif [ -x "/Applications/Blender.app/Contents/MacOS/Blender" ]; then
    BLENDER_BIN="/Applications/Blender.app/Contents/MacOS/Blender"
  else
    echo "Blender が見つかりません。BLENDER_BIN に Blender 実行ファイルのパスを指定してください。" >&2
    exit 1
  fi
fi

TARGET="${BLENDER_GENERATE_TARGET:-video}"
OUTPUT_PATH="${BLENDER_VIDEO_OUTPUT:-export/update.mp4}"
SHORTS_OUTPUT_PATH="${BLENDER_SHORTS_OUTPUT:-export/update-shorts.mp4}"
GENERATED_AT="$(date '+%Y-%m-%d %H:%M:%S')"
TITLE="${BLENDER_VIDEO_TITLE:-VRM更新動画 ${GENERATED_AT}}"
MESSAGE="${BLENDER_VIDEO_MESSAGE:-Blender が import/avator.vrm を読み込んで生成した更新紹介動画です。}"
SHORTS_TITLE="${BLENDER_SHORTS_TITLE:-VRM更新Shorts ${GENERATED_AT} #Shorts}"
SHORTS_MESSAGE="${BLENDER_SHORTS_MESSAGE:-VRM素材から生成した要約Shortsです。}"
DURATION="${BLENDER_VIDEO_DURATION:-10}"
SHORTS_DURATION="${BLENDER_SHORTS_DURATION:-5}"

case "${TARGET}" in
  video | shorts | both) ;;
  *)
    echo "BLENDER_GENERATE_TARGET must be video, shorts, or both: ${TARGET}" >&2
    exit 1
    ;;
esac

case "${OUTPUT_PATH}" in
  /*) OUTPUT_FILE="${OUTPUT_PATH}" ;;
  *) OUTPUT_FILE="${REPO_ROOT}/${OUTPUT_PATH}" ;;
esac
case "${SHORTS_OUTPUT_PATH}" in
  /*) SHORTS_OUTPUT_FILE="${SHORTS_OUTPUT_PATH}" ;;
  *) SHORTS_OUTPUT_FILE="${REPO_ROOT}/${SHORTS_OUTPUT_PATH}" ;;
esac

"${BLENDER_BIN}" \
  --background \
  --factory-startup \
  --python "${REPO_ROOT}/scripts/render_vrm_with_blender.py" \
  -- \
  --repo-root "${REPO_ROOT}" \
  --target "${TARGET}" \
  --output "${OUTPUT_PATH}" \
  --shorts-output "${SHORTS_OUTPUT_PATH}" \
  --duration "${DURATION}" \
  --shorts-duration "${SHORTS_DURATION}" \
  --title "${TITLE}" \
  --message "${MESSAGE}" \
  --shorts-title "${SHORTS_TITLE}" \
  --shorts-message "${SHORTS_MESSAGE}"

case "${TARGET}" in
  video)
    test -s "${OUTPUT_FILE}"
    ;;
  shorts)
    test -s "${SHORTS_OUTPUT_FILE}"
    ;;
  both)
    test -s "${OUTPUT_FILE}"
    test -s "${SHORTS_OUTPUT_FILE}"
    ;;
esac

echo "Blender video generation completed: ${TARGET}"
