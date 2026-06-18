@echo off
setlocal EnableDelayedExpansion
REM Codex CLI が使えない環境では動画生成を開始せずに終了します。
where codex >nul 2>nul
if errorlevel 1 (
  echo codex command was not found. Install and sign in to Codex CLI first.
  exit /b 1
)

REM CODEX_* 環境変数が未指定の場合はサンプル用の初期値を使います。
if "%CODEX_VIDEO_OUTPUT%"=="" set "CODEX_VIDEO_OUTPUT=export\update.mp4"
if "%CODEX_SHORTS_OUTPUT%"=="" set "CODEX_SHORTS_OUTPUT=export\update-shorts.mp4"
if "%CODEX_IMPORT_IMAGE%"=="" set "CODEX_IMPORT_IMAGE=import\avator.png"
if "%CODEX_GENERATE_TARGET%"=="" set "CODEX_GENERATE_TARGET=video"
if "%CODEX_VIDEO_TITLE%"=="" set "CODEX_VIDEO_TITLE=萌え更新速報 %DATE% %TIME%"
if "%CODEX_VIDEO_MESSAGE%"=="" set "CODEX_VIDEO_MESSAGE=Codex CLI が作成した新しい更新紹介動画です。"
if "%CODEX_VIDEO_DURATION%"=="" set "CODEX_VIDEO_DURATION=10"
if "%CODEX_SHORTS_TITLE%"=="" set "CODEX_SHORTS_TITLE=萌え更新速報 Shorts %DATE% %TIME%"
if "%CODEX_SHORTS_MESSAGE%"=="" set "CODEX_SHORTS_MESSAGE=通常動画の内容を5秒で要約したShortsです。"
if "%CODEX_SHORTS_DURATION%"=="" set "CODEX_SHORTS_DURATION=5"
if "%CODEX_VIDEO_STYLE%"=="" (
  REM 目の位置ずれを避けるため、キャラクター描画時の座標条件を明示します。
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
REM scripts/make_video.py を使わず、Codex CLI に MP4 の直接生成だけを依頼します。
codex exec ^
  --cd "%CD%" ^
  --sandbox workspace-write ^
  "このリポジトリで、ChatGPT / Codex の判断だけで指定された MP4 動画を作成してください。生成対象は %CODEX_GENERATE_TARGET% です。video は通常動画のみ、shorts は Shorts のみ、both は両方を意味します。scripts/make_video.py、scripts/create_sample_video.sh、scripts/create_sample_video.bat は使用しないでください。ffmpeg など利用可能なコマンドを自分で選び、通常動画は %CODEX_VIDEO_OUTPUT% に横長 16:9、1280x720、%CODEX_VIDEO_DURATION% 秒程度で作成してください。Shorts 用動画は %CODEX_SHORTS_OUTPUT% に縦長 9:16、1080x1920、%CODEX_SHORTS_DURATION% 秒程度で作成してください。%CODEX_IMPORT_IMAGE% が存在する場合は、その画像を主要キャラクター素材として必ず使用してください。import ディレクトリに *.vrm が存在する場合は、可能なら VRM を主要キャラクター素材として使ってください。VRM を直接レンダリングできるコマンドが無い場合は、VRM ファイル名を画面内に示し、%CODEX_IMPORT_IMAGE% など利用可能なプレビュー画像を使って動画化してください。import ディレクトリに *.unitypackage が存在する場合は、可能なら中身を調べて使える画像やモデル素材を利用してください。Unity が無い環境で直接開けない場合は、unitypackage ファイル名を画面内に示し、利用可能な画像素材で代替してください。通常動画にはタイトル「%CODEX_VIDEO_TITLE%」と補足「%CODEX_VIDEO_MESSAGE%」を表示してください。Shorts にはタイトル「%CODEX_SHORTS_TITLE%」と補足「%CODEX_SHORTS_MESSAGE%」を表示し、通常動画の要点を短くまとめてください。ビジュアルは「%CODEX_VIDEO_STYLE%」にしてください。どちらも単なる文字だけの動画にはせず、背景、タイトル、装飾、ズーム、パン、フェード、軽い揺れなどの演出を追加してください。export ディレクトリが無ければ作成してください。動画生成に必要なコマンド実行以外の repository ファイル編集はしないでください。最後に生成対象に含まれる出力ファイルが存在し、空ファイルではないことを確認してください。"
set "CODEX_RESULT=%ERRORLEVEL%"
if not "%CODEX_RESULT%"=="0" (
  popd
  exit /b %CODEX_RESULT%
)
REM 生成対象のファイルが存在し、空ファイルではないことを確認します。
if /I "%CODEX_GENERATE_TARGET%"=="shorts" goto check_shorts
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
if /I "%CODEX_GENERATE_TARGET%"=="video" goto done

:check_shorts
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

:done
popd
exit /b 0
