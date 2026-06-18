#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BLENDER_BIN="${BLENDER_BIN:-}"

# BLENDER_BIN が未指定の場合は PATH、macOS 標準配置の順に Blender を探します。
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

# 環境変数で通常動画、Shorts、両方の生成対象と出力先を切り替えます。
TARGET="${BLENDER_GENERATE_TARGET:-video}"
GPU_BACKEND="${BLENDER_GPU_BACKEND:-opengl}"
RENDER_MODE="${BLENDER_RENDER_MODE:-viewport}"
OUTPUT_PATH="${BLENDER_VIDEO_OUTPUT:-export/update.mp4}"
SHORTS_OUTPUT_PATH="${BLENDER_SHORTS_OUTPUT:-export/update-shorts.mp4}"
GENERATED_AT="$(date '+%Y-%m-%d %H:%M:%S')"
TITLE="${BLENDER_VIDEO_TITLE:-Radio Taiso VRM ${GENERATED_AT}}"
MESSAGE="${BLENDER_VIDEO_MESSAGE:-Blender が import/avator.vrm を読み込み、30秒のラジオ体操風モーションを生成しました。}"
SHORTS_TITLE="${BLENDER_SHORTS_TITLE:-VRM更新Shorts ${GENERATED_AT} #Shorts}"
SHORTS_MESSAGE="${BLENDER_SHORTS_MESSAGE:-VRM素材から生成した要約Shortsです。}"
DURATION="${BLENDER_VIDEO_DURATION:-30}"
SHORTS_DURATION="${BLENDER_SHORTS_DURATION:-5}"

case "${TARGET}" in
  video | shorts | both) ;;
  *)
    echo "BLENDER_GENERATE_TARGET must be video, shorts, or both: ${TARGET}" >&2
    exit 1
    ;;
esac

# Blender 側の script へ渡す前に、検証用の絶対パスも用意します。
case "${OUTPUT_PATH}" in
  /*) OUTPUT_FILE="${OUTPUT_PATH}" ;;
  *) OUTPUT_FILE="${REPO_ROOT}/${OUTPUT_PATH}" ;;
esac
case "${SHORTS_OUTPUT_PATH}" in
  /*) SHORTS_OUTPUT_FILE="${SHORTS_OUTPUT_PATH}" ;;
  *) SHORTS_OUTPUT_FILE="${REPO_ROOT}/${SHORTS_OUTPUT_PATH}" ;;
esac

BLENDER_ARGS=(
  --gpu-backend "${GPU_BACKEND}"
  --factory-startup
  --python "${REPO_ROOT}/scripts/render_vrm_with_blender.py"
  --
  --repo-root "${REPO_ROOT}"
  --target "${TARGET}"
  --output "${OUTPUT_PATH}"
  --shorts-output "${SHORTS_OUTPUT_PATH}"
  --duration "${DURATION}"
  --shorts-duration "${SHORTS_DURATION}"
  --title "${TITLE}"
  --message "${MESSAGE}"
  --shorts-title "${SHORTS_TITLE}"
  --shorts-message "${SHORTS_MESSAGE}"
  --render-mode "${RENDER_MODE}"
)

render_viewport_animation() {
  # prepare mode で保存した .blend を開き、viewport render で軽量に MP4 を出力します。
  local blend_file="$1"
  local output_file="$2"

  "${BLENDER_BIN}" \
    --gpu-backend "${GPU_BACKEND}" \
    --factory-startup \
    "${blend_file}" \
    --python-expr "import bpy; bpy.context.scene.render.filepath='${output_file}'; bpy.ops.render.opengl(animation=True, view_context=False); print('viewport_animation_ok'); bpy.ops.wm.quit_blender()"
}

overlay_video_metadata() {
  # GitHub 上で動画を見たときに生成元が分かるよう、上下にタイトルと素材情報を焼き込みます。
  local output_file="$1"
  local title_text="$2"
  local source_text="$3"

  if ! command -v ffmpeg >/dev/null 2>&1; then
    return
  fi

  local tmp_dir
  tmp_dir="$(mktemp -d)"
  printf '%s\n' "${title_text}" > "${tmp_dir}/title.txt"
  printf '%s\n' "${source_text}" > "${tmp_dir}/source.txt"

  ffmpeg -y \
    -i "${output_file}" \
    -vf "drawbox=x=0:y=0:w=iw:h=86:color=0x20233a@0.82:t=fill,drawbox=x=0:y=638:w=iw:h=82:color=0x20233a@0.82:t=fill,drawtext=fontfile=/System/Library/Fonts/AppleSDGothicNeo.ttc:textfile=${tmp_dir}/title.txt:fontcolor=white:fontsize=42:x=(w-text_w)/2:y=24,drawtext=fontfile=/System/Library/Fonts/AppleSDGothicNeo.ttc:textfile=${tmp_dir}/source.txt:fontcolor=white:fontsize=26:x=(w-text_w)/2:y=666" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -movflags +faststart \
    -c:a copy \
    "${tmp_dir}/overlay.mp4"
  mv "${tmp_dir}/overlay.mp4" "${output_file}"
}

if [ "${RENDER_MODE}" = "viewport" ]; then
  # viewport mode はまず scene を .blend として準備し、その後 OpenGL render で動画化します。
  PREPARE_ARGS=("${BLENDER_ARGS[@]}")
  PREPARE_ARGS[${#PREPARE_ARGS[@]}-1]="prepare"
  "${BLENDER_BIN}" --background "${PREPARE_ARGS[@]}"
  if [ "${TARGET}" = "video" ] || [ "${TARGET}" = "both" ]; then
    render_viewport_animation "${OUTPUT_FILE%.mp4}.blend" "${OUTPUT_FILE}"
    overlay_video_metadata "${OUTPUT_FILE}" "${TITLE}" "radio exercise / source: import/avator.vrm + import/avator.unitypackage / viewport render"
  fi
  if [ "${TARGET}" = "shorts" ] || [ "${TARGET}" = "both" ]; then
    render_viewport_animation "${SHORTS_OUTPUT_FILE%.mp4}.blend" "${SHORTS_OUTPUT_FILE}"
    overlay_video_metadata "${SHORTS_OUTPUT_FILE}" "${SHORTS_TITLE}" "source: import/avator.vrm + import/avator.unitypackage / viewport render"
  fi
elif [ "${RENDER_MODE}" = "final" ]; then
  # final mode は Blender の通常レンダーをそのまま実行します。
  "${BLENDER_BIN}" --background "${BLENDER_ARGS[@]}"
else
  echo "BLENDER_RENDER_MODE must be viewport or final: ${RENDER_MODE}" >&2
  exit 1
fi

# 指定された生成対象のファイルが空ではないことを最後に確認します。
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
