#!/usr/bin/env bash
set -euo pipefail

if ! command -v codex >/dev/null 2>&1; then
  echo "codex command was not found. Install and sign in to Codex CLI first." >&2
  exit 1
fi

OUTPUT_PATH="${CODEX_VIDEO_OUTPUT:-export/update.mp4}"
SHORTS_OUTPUT_PATH="${CODEX_SHORTS_OUTPUT:-export/update-shorts.mp4}"
IMPORT_IMAGE_PATH="${CODEX_IMPORT_IMAGE:-import/avator.png}"
GENERATED_AT="$(date '+%Y-%m-%d %H:%M:%S')"
TITLE="${CODEX_VIDEO_TITLE:-萌え更新速報 ${GENERATED_AT}}"
MESSAGE="${CODEX_VIDEO_MESSAGE:-Codex CLI が作成した新しい更新紹介動画です。}"
DURATION="${CODEX_VIDEO_DURATION:-10}"
SHORTS_TITLE="${CODEX_SHORTS_TITLE:-萌え更新速報 Shorts ${GENERATED_AT}}"
SHORTS_MESSAGE="${CODEX_SHORTS_MESSAGE:-通常動画の内容を5秒で要約したShortsです。}"
SHORTS_DURATION="${CODEX_SHORTS_DURATION:-5}"
DEFAULT_STYLE="$(cat <<'EOF'
一般的なフリー素材風のアニメ立ち絵を参考にした、完全オリジナルの萌え系女子キャラクター。
顔は画面中央付近に配置し、輪郭、髪、目、口、服の順で破綻なく重ねる。
大きな瞳は左右同じ高さで、必ず顔の内側に配置する。目が顔から飛び出したり、左右で極端にズレたりしないようにする。
瞳の外側の円も顔の輪郭の内側に完全に収める。瞳は顔の下端ではなく、顔の中央より少し上に置く。
顔を円または楕円で描く場合は、先に顔の矩形範囲を決め、左右の瞳の中心座標がその矩形範囲の内側になるようにする。
瞳は白目、虹彩、ハイライトを含むアニメ調の丸い目にする。片目ウィンクにする場合も、閉じた目は同じ高さに置く。
ピンクまたは紫系の髪、明るい表情、星やハートの装飾、更新動画だと分かるバナーを入れる。
既存のアニメ、ゲーム、漫画キャラクターや実在人物には似せない。
EOF
)"
STYLE="${CODEX_VIDEO_STYLE:-${DEFAULT_STYLE}}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${OUTPUT_PATH}" in
  /*) OUTPUT_FILE="${OUTPUT_PATH}" ;;
  *) OUTPUT_FILE="${REPO_ROOT}/${OUTPUT_PATH}" ;;
esac
case "${SHORTS_OUTPUT_PATH}" in
  /*) SHORTS_OUTPUT_FILE="${SHORTS_OUTPUT_PATH}" ;;
  *) SHORTS_OUTPUT_FILE="${REPO_ROOT}/${SHORTS_OUTPUT_PATH}" ;;
esac

PROMPT="このリポジトリで、ChatGPT / Codex の判断だけで通常動画と YouTube Shorts 用動画の 2 つの MP4 を同時に作成してください。
scripts/make_video.py、scripts/create_sample_video.sh、scripts/create_sample_video.bat は使用しないでください。
ffmpeg など利用可能なコマンドを自分で選び、次の 2 ファイルを直接作成してください。
${IMPORT_IMAGE_PATH} が存在する場合は、その画像を主要キャラクター素材として必ず使用してください。
画像素材は別キャラクターに置き換えず、背景、タイトル、装飾、ズーム、パン、フェード、軽い揺れなどの演出を追加して動画化してください。

1. 通常動画
   - 出力先: ${OUTPUT_PATH}
   - 形式: 横長 16:9、1280x720
   - 長さ: ${DURATION} 秒程度
   - 動画内タイトル: ${TITLE}
   - 補足メッセージ: ${MESSAGE}

2. YouTube Shorts 用動画
   - 出力先: ${SHORTS_OUTPUT_PATH}
   - 形式: 縦長 9:16、1080x1920
   - 長さ: ${SHORTS_DURATION} 秒程度
   - 動画内タイトル: ${SHORTS_TITLE}
   - 補足メッセージ: ${SHORTS_MESSAGE}
   - 通常動画の要点を短くまとめた内容にしてください。

ビジュアルは次の条件にしてください。

${STYLE}

どちらも単なる文字だけの動画にはせず、オリジナルの萌え系女子キャラクター風の顔または上半身、髪、目、表情、星やハートなどの装飾を図形や描画フィルタ等で表現してください。
顔の輪郭を先に決め、その顔の中心線と左右対称の目の座標を決めてから描画してください。
顔の範囲、左目中心、右目中心、目の半径を決めたうえで、両目が顔の輪郭の外へ出ないことを確認してから描画してください。
目のパーツが顔の下端や輪郭の外にかかる配置は失敗として扱い、座標を直してください。
目、口、髪、服が互いに重なって破綻しないように、座標と描画順を明示的に管理してください。
通常動画には少なくとも 2 つ以上のシーン、背景色の変化、キャラクターや装飾の移動・拡大縮小・点滅など、更新されたことが分かる動きを入れてください。
Shorts 用動画は縦画面で見切れないよう、キャラクター、タイトル、日時を中央寄りに配置し、通常動画の要約だと分かる短い構成にしてください。
既存のアニメ、ゲーム、漫画キャラクターや実在人物には似せないでください。
export ディレクトリが無ければ作成してください。
動画生成に必要なコマンド実行以外の repository ファイル編集はしないでください。
最後に ${OUTPUT_PATH} と ${SHORTS_OUTPUT_PATH} が存在し、どちらも空ファイルではないことを確認してください。"

codex exec \
  --cd "${REPO_ROOT}" \
  --sandbox workspace-write \
  "${PROMPT}"

if [ ! -s "${OUTPUT_FILE}" ]; then
  echo "Codex CLI did not create a video file: ${OUTPUT_PATH}" >&2
  exit 1
fi

if [ ! -s "${SHORTS_OUTPUT_FILE}" ]; then
  echo "Codex CLI did not create a Shorts video file: ${SHORTS_OUTPUT_PATH}" >&2
  exit 1
fi

echo "Codex CLI created video: ${OUTPUT_PATH}"
echo "Codex CLI created Shorts video: ${SHORTS_OUTPUT_PATH}"
