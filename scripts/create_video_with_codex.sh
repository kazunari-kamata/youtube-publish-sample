#!/usr/bin/env bash
set -euo pipefail

if ! command -v codex >/dev/null 2>&1; then
  echo "codex command was not found. Install and sign in to Codex CLI first." >&2
  exit 1
fi

OUTPUT_PATH="${CODEX_VIDEO_OUTPUT:-output/update.mp4}"
GENERATED_AT="$(date '+%Y-%m-%d %H:%M:%S')"
TITLE="${CODEX_VIDEO_TITLE:-萌え更新速報 ${GENERATED_AT}}"
MESSAGE="${CODEX_VIDEO_MESSAGE:-Codex CLI が作成した新しい更新紹介動画です。}"
DURATION="${CODEX_VIDEO_DURATION:-5}"
DEFAULT_STYLE="$(cat <<'EOF'
一般的なフリー素材風のアニメ立ち絵を参考にした、完全オリジナルの萌え系女子キャラクター。
顔は画面中央付近に配置し、輪郭、髪、目、口、服の順で破綻なく重ねる。
大きな瞳は左右同じ高さで、必ず顔の内側に配置する。目が顔から飛び出したり、左右で極端にズレたりしないようにする。
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

PROMPT="このリポジトリで、ChatGPT / Codex の判断だけで短い MP4 動画を作成してください。
scripts/make_video.py、scripts/create_sample_video.sh、scripts/create_sample_video.bat は使用しないでください。
ffmpeg など利用可能なコマンドを自分で選び、出力先 ${OUTPUT_PATH} に動画ファイルを直接作成してください。
長さは ${DURATION} 秒です。
動画内に、毎回違う動画だと分かる大きなタイトル「${TITLE}」と、補足メッセージ「${MESSAGE}」を必ず表示してください。
ビジュアルは次の条件にしてください。

${STYLE}

単なる文字だけの動画にはせず、オリジナルの萌え系女子キャラクター風の顔または上半身、髪、目、表情、星やハートなどの装飾を図形や描画フィルタ等で表現してください。
顔の輪郭を先に決め、その顔の中心線と左右対称の目の座標を決めてから描画してください。
目、口、髪、服が互いに重なって破綻しないように、座標と描画順を明示的に管理してください。
少なくとも 2 つ以上のシーン、背景色の変化、キャラクターや装飾の移動・拡大縮小・点滅など、更新されたことが分かる動きを入れてください。
既存のアニメ、ゲーム、漫画キャラクターや実在人物には似せないでください。
output ディレクトリが無ければ作成してください。
動画生成に必要なコマンド実行以外の repository ファイル編集はしないでください。
最後に ${OUTPUT_PATH} が存在し、空ファイルではないことを確認してください。"

codex exec \
  --cd "${REPO_ROOT}" \
  --sandbox workspace-write \
  "${PROMPT}"

if [ ! -s "${OUTPUT_FILE}" ]; then
  echo "Codex CLI did not create a video file: ${OUTPUT_PATH}" >&2
  exit 1
fi

echo "Codex CLI created video: ${OUTPUT_PATH}"
