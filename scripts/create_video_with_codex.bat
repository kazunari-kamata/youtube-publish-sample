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
codex exec --cd "%CD%" --sandbox workspace-write "このリポジトリで、既存の scripts/make_video.py を使って短い MP4 動画を作成してください。出力先は %CODEX_VIDEO_OUTPUT%、タイトルは「%CODEX_VIDEO_TITLE%」、メッセージは「%CODEX_VIDEO_MESSAGE%」、長さは %CODEX_VIDEO_DURATION% 秒です。output ディレクトリが無ければ作成してください。動画生成以外のファイル編集はしないでください。"
set "CODEX_RESULT=%ERRORLEVEL%"
popd
exit /b %CODEX_RESULT%
