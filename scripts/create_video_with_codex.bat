@echo off
where codex >nul 2>nul
if errorlevel 1 (
  echo codex command was not found. Install and sign in to Codex CLI first.
  exit /b 1
)

if "%CODEX_VIDEO_OUTPUT%"=="" set "CODEX_VIDEO_OUTPUT=output\update.mp4"
if "%CODEX_VIDEO_TITLE%"=="" set "CODEX_VIDEO_TITLE=Codex CLI 動画生成テスト"
if "%CODEX_VIDEO_MESSAGE%"=="" set "CODEX_VIDEO_MESSAGE=ChatGPT / Codex CLI から生成した短いサンプル動画です。"
if "%CODEX_VIDEO_DURATION%"=="" set "CODEX_VIDEO_DURATION=3"

pushd "%~dp0.."
codex exec --cd "%CD%" --sandbox workspace-write "このリポジトリで、ChatGPT / Codex の判断だけで短い MP4 動画を作成してください。scripts/make_video.py、scripts/create_sample_video.sh、scripts/create_sample_video.bat は使用しないでください。ffmpeg など利用可能なコマンドを自分で選び、出力先 %CODEX_VIDEO_OUTPUT% に動画ファイルを直接作成してください。タイトルは「%CODEX_VIDEO_TITLE%」、メッセージは「%CODEX_VIDEO_MESSAGE%」、長さは %CODEX_VIDEO_DURATION% 秒です。output ディレクトリが無ければ作成してください。動画生成に必要なコマンド実行以外の repository ファイル編集はしないでください。最後に %CODEX_VIDEO_OUTPUT% が存在し、空ファイルではないことを確認してください。"
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
