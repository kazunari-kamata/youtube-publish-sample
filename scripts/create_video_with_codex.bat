@echo off
setlocal EnableDelayedExpansion
where codex >nul 2>nul
if errorlevel 1 (
  echo codex command was not found. Install and sign in to Codex CLI first.
  exit /b 1
)

if "%CODEX_VIDEO_OUTPUT%"=="" set "CODEX_VIDEO_OUTPUT=output\update.mp4"
if "%CODEX_SHORTS_OUTPUT%"=="" set "CODEX_SHORTS_OUTPUT=output\update-shorts.mp4"
if "%CODEX_VIDEO_TITLE%"=="" set "CODEX_VIDEO_TITLE=萌え更新速報 %DATE% %TIME%"
if "%CODEX_VIDEO_MESSAGE%"=="" set "CODEX_VIDEO_MESSAGE=Codex CLI が作成した新しい更新紹介動画です。"
if "%CODEX_VIDEO_DURATION%"=="" set "CODEX_VIDEO_DURATION=10"
if "%CODEX_SHORTS_TITLE%"=="" set "CODEX_SHORTS_TITLE=萌え更新速報 Shorts %DATE% %TIME%"
if "%CODEX_SHORTS_MESSAGE%"=="" set "CODEX_SHORTS_MESSAGE=通常動画の内容を5秒で要約したShortsです。"
if "%CODEX_SHORTS_DURATION%"=="" set "CODEX_SHORTS_DURATION=5"
if "%CODEX_VIDEO_STYLE%"=="" (
  set "CODEX_VIDEO_STYLE=一般的なフリー素材風のアニメ立ち絵を参考にした、完全オリジナルの萌え系女子キャラクター。"
  set "CODEX_VIDEO_STYLE=!CODEX_VIDEO_STYLE! 顔は画面中央付近に配置し、輪郭、髪、目、口、服の順で破綻なく重ねる。"
  set "CODEX_VIDEO_STYLE=!CODEX_VIDEO_STYLE! 大きな瞳は左右同じ高さで、必ず顔の内側に配置する。目が顔から飛び出したり、左右で極端にズレたりしないようにする。"
  set "CODEX_VIDEO_STYLE=!CODEX_VIDEO_STYLE! 瞳の外側の円も顔の輪郭の内側に完全に収める。瞳は顔の下端ではなく、顔の中央より少し上に置く。"
  set "CODEX_VIDEO_STYLE=!CODEX_VIDEO_STYLE! 顔を円または楕円で描く場合は、先に顔の矩形範囲を決め、左右の瞳の中心座標がその矩形範囲の内側になるようにする。"
  set "CODEX_VIDEO_STYLE=!CODEX_VIDEO_STYLE! 瞳は白目、虹彩、ハイライトを含むアニメ調の丸い目にする。片目ウィンクにする場合も、閉じた目は同じ高さに置く。"
  set "CODEX_VIDEO_STYLE=!CODEX_VIDEO_STYLE! ピンクまたは紫系の髪、明るい表情、星やハートの装飾、更新動画だと分かるバナーを入れる。"
  set "CODEX_VIDEO_STYLE=!CODEX_VIDEO_STYLE! 既存のアニメ、ゲーム、漫画キャラクターや実在人物には似せない。"
)

pushd "%~dp0.."
codex exec ^
  --cd "%CD%" ^
  --sandbox workspace-write ^
  "このリポジトリで、ChatGPT / Codex の判断だけで通常動画と YouTube Shorts 用動画の 2 つの MP4 を同時に作成してください。scripts/make_video.py、scripts/create_sample_video.sh、scripts/create_sample_video.bat は使用しないでください。ffmpeg など利用可能なコマンドを自分で選び、通常動画は %CODEX_VIDEO_OUTPUT% に横長 16:9、1280x720、%CODEX_VIDEO_DURATION% 秒程度で作成してください。Shorts 用動画は %CODEX_SHORTS_OUTPUT% に縦長 9:16、1080x1920、%CODEX_SHORTS_DURATION% 秒程度で作成してください。通常動画にはタイトル「%CODEX_VIDEO_TITLE%」と補足「%CODEX_VIDEO_MESSAGE%」を表示してください。Shorts にはタイトル「%CODEX_SHORTS_TITLE%」と補足「%CODEX_SHORTS_MESSAGE%」を表示し、通常動画の要点を短くまとめてください。ビジュアルは「%CODEX_VIDEO_STYLE%」にしてください。どちらも単なる文字だけの動画にはせず、オリジナルの萌え系女子キャラクター風の顔または上半身、髪、目、表情、星やハートなどの装飾を図形や描画フィルタ等で表現してください。顔の輪郭を先に決め、その顔の中心線と左右対称の目の座標を決めてから描画してください。顔の範囲、左目中心、右目中心、目の半径を決めたうえで、両目が顔の輪郭の外へ出ないことを確認してから描画してください。目のパーツが顔の下端や輪郭の外にかかる配置は失敗として扱い、座標を直してください。目、口、髪、服が互いに重なって破綻しないように、座標と描画順を明示的に管理してください。通常動画には少なくとも 2 つ以上のシーン、背景色の変化、キャラクターや装飾の移動・拡大縮小・点滅など、更新されたことが分かる動きを入れてください。Shorts 用動画は縦画面で見切れないよう、キャラクター、タイトル、日時を中央寄りに配置してください。既存のアニメ、ゲーム、漫画キャラクターや実在人物には似せないでください。output ディレクトリが無ければ作成してください。動画生成に必要なコマンド実行以外の repository ファイル編集はしないでください。最後に %CODEX_VIDEO_OUTPUT% と %CODEX_SHORTS_OUTPUT% が存在し、どちらも空ファイルではないことを確認してください。"
set "CODEX_RESULT=%ERRORLEVEL%"
if not "%CODEX_RESULT%"=="0" (
  popd
  exit /b %CODEX_RESULT%
)
if not exist "%CODEX_VIDEO_OUTPUT%" (
  echo Codex CLI did not create a video file: %CODEX_VIDEO_OUTPUT%
  popd
  exit /b 1
)
for %%A in ("%CODEX_VIDEO_OUTPUT%") do if %%~zA==0 (
  echo Codex CLI created an empty video file: %CODEX_VIDEO_OUTPUT%
  popd
  exit /b 1
)
echo Codex CLI created video: %CODEX_VIDEO_OUTPUT%
if not exist "%CODEX_SHORTS_OUTPUT%" (
  echo Codex CLI did not create a Shorts video file: %CODEX_SHORTS_OUTPUT%
  popd
  exit /b 1
)
for %%A in ("%CODEX_SHORTS_OUTPUT%") do if %%~zA==0 (
  echo Codex CLI created an empty Shorts video file: %CODEX_SHORTS_OUTPUT%
  popd
  exit /b 1
)
echo Codex CLI created Shorts video: %CODEX_SHORTS_OUTPUT%
popd
exit /b 0
