@echo off
where codex >nul 2>nul
if errorlevel 1 (
  echo codex command was not found. Install and sign in to Codex CLI first.
  exit /b 1
)

if "%CODEX_VIDEO_OUTPUT%"=="" set "CODEX_VIDEO_OUTPUT=output\update.mp4"
if "%CODEX_VIDEO_TITLE%"=="" set "CODEX_VIDEO_TITLE=萌え更新速報 %DATE% %TIME%"
if "%CODEX_VIDEO_MESSAGE%"=="" set "CODEX_VIDEO_MESSAGE=Codex CLI が作成した新しい更新紹介動画です。"
if "%CODEX_VIDEO_DURATION%"=="" set "CODEX_VIDEO_DURATION=5"
if "%CODEX_VIDEO_STYLE%"=="" set "CODEX_VIDEO_STYLE=オリジナルの萌え系女子キャラクター。ピンク髪、ツインテール、大きな瞳、笑顔、星やハートの装飾。既存作品や実在人物に似せない。"

pushd "%~dp0.."
codex exec --cd "%CD%" --sandbox workspace-write "このリポジトリで、ChatGPT / Codex の判断だけで短い MP4 動画を作成してください。scripts/make_video.py、scripts/create_sample_video.sh、scripts/create_sample_video.bat は使用しないでください。ffmpeg など利用可能なコマンドを自分で選び、出力先 %CODEX_VIDEO_OUTPUT% に動画ファイルを直接作成してください。長さは %CODEX_VIDEO_DURATION% 秒です。動画内に、毎回違う動画だと分かる大きなタイトル「%CODEX_VIDEO_TITLE%」と、補足メッセージ「%CODEX_VIDEO_MESSAGE%」を必ず表示してください。ビジュアルは「%CODEX_VIDEO_STYLE%」にしてください。単なる文字だけの動画にはせず、オリジナルの萌え系女子キャラクター風の顔または上半身、髪、目、表情、星やハートなどの装飾を図形や描画フィルタ等で表現してください。少なくとも 2 つ以上のシーン、背景色の変化、キャラクターや装飾の移動・拡大縮小・点滅など、更新されたことが分かる動きを入れてください。既存のアニメ、ゲーム、漫画キャラクターや実在人物には似せないでください。output ディレクトリが無ければ作成してください。動画生成に必要なコマンド実行以外の repository ファイル編集はしないでください。最後に %CODEX_VIDEO_OUTPUT% が存在し、空ファイルではないことを確認してください。"
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
popd
exit /b 0
