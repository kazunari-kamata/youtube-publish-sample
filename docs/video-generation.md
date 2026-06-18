# ローカル動画生成と push 手順

## ローカル動画を push してアップロードする

Codex CLI などでローカルに `export/update.mp4` と `export/update-shorts.mp4` を作成し、そのファイルを repository に commit して `main` に push すると、GitHub Actions が自動で YouTube に限定公開アップロードします。この方式では GitHub Actions 内で Codex CLI や ChatGPT 用の API token は使いません。GitHub Actions は、push 済みの動画ファイルを受け取って YouTube Data API でアップロードするだけです。

`import/avator.png` が存在する場合、`scripts/create_video_with_codex.sh` / `scripts/create_video_with_codex.bat` はその画像を主要キャラクター素材として使うよう Codex CLI に依頼します。`import/*.vrm` や `import/*.unitypackage` が存在する場合も、利用可能なレンダリング環境があればその素材を使い、直接レンダリングできない場合はファイル名を示しつつプレビュー画像などで動画化するよう依頼します。入力素材は `import/`、アップロード対象の完成動画は `export/` に分けています。

`*.vrm` と `*.unitypackage` はサイズが大きくなりやすいため、初期設定では `.gitignore` の対象です。ローカル生成用の入力素材として `import/` に置き、完成した `export/update.mp4` や `export/update-shorts.mp4` だけを commit する運用を想定しています。

### Blender で VRM から動画を生成する

Blender がインストールされ、CLI から起動できる場合は、Codex CLI を使わずに `import/*.vrm` を直接読み込んで動画を生成できます。

```bash
./scripts/create_video_with_blender.sh
```

初期値では通常動画だけを `export/update.mp4` に生成します。Shorts だけ、または両方を生成したい場合は `BLENDER_GENERATE_TARGET` を指定します。

```bash
BLENDER_GENERATE_TARGET=shorts ./scripts/create_video_with_blender.sh
BLENDER_GENERATE_TARGET=both ./scripts/create_video_with_blender.sh
```

`blender` コマンドが PATH に無い場合でも、macOS の `/Applications/Blender.app/Contents/MacOS/Blender` が存在すれば自動検出します。別の場所にインストールしている場合は `BLENDER_BIN` を指定してください。

```bash
BLENDER_BIN="/Applications/Blender.app/Contents/MacOS/Blender" ./scripts/create_video_with_blender.sh
```

Blender 3.6 系の macOS 版では、初期値として `--gpu-backend opengl` を付けて起動します。Metal で問題なく動く環境では `BLENDER_GPU_BACKEND=metal` を指定できます。

```bash
BLENDER_GPU_BACKEND=metal ./scripts/create_video_with_blender.sh
```

この Blender 生成では、`import/*.vrm` を glTF として Blender に読み込み、モデルを回転させる動画を作成します。`import/*.unitypackage` がある場合は asset 数を読み取り、動画内のメタ情報として表示します。UnityPackage の prefab や scene を完全に再現する処理ではありません。

Blender 4.5 以降の macOS 版は GPU backend が Metal のみです。環境によっては background 起動直後に Metal 初期化で `Segmentation fault` になることがあります。その場合は、Blender 3.6 LTS など `--gpu-backend opengl` が使える旧版を使うか、Unity 側で素材を確認してから完成動画を書き出してください。

### UnityPackage を使う場合

Unity を使う場合は、`import/*.unitypackage` を Unity project に import して prefab、scene、texture、animation を確認できます。Unity で確認・調整した結果を動画として書き出し、完成した MP4 を `export/update.mp4` または `export/update-shorts.mp4` として commit してください。

Unity の batchmode はライセンス確認や初回起動設定が必要です。macOS で Unity Hub から入れた Editor は、次のように確認できます。

```bash
/Applications/Unity/Hub/Editor/6000.5.0f1/Unity.app/Contents/MacOS/Unity \
  -batchmode \
  -nographics \
  -quit \
  -logFile - \
  -version
```

Unity Recorder などで動画を書き出す構成はプロジェクト依存になりやすいため、このサンプルでは完成済み MP4 を `export/` に置いて GitHub Actions からアップロードする方式を基本にしています。

手順:

1. Blender または Codex CLI で動画を作成します。

   ```bash
   ./scripts/create_video_with_blender.sh
   ./scripts/create_video_with_codex.sh
   ```

   初期値では通常動画だけを生成します。Shorts だけ、または両方を生成したい場合は `CODEX_GENERATE_TARGET` を指定します。

   ```bash
   CODEX_GENERATE_TARGET=shorts ./scripts/create_video_with_codex.sh
   CODEX_GENERATE_TARGET=both ./scripts/create_video_with_codex.sh
   ```

2. 動画ファイルを確認します。

   ```bash
   ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,nb_frames -of default=noprint_wrappers=1 export/update.mp4
   ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,nb_frames -of default=noprint_wrappers=1 export/update-shorts.mp4
   ```

3. YouTube 側のタイトルや説明文、アップロード対象を指定したい場合は、任意で metadata ファイルを作成します。不要な場合はこの手順を省略してください。

   ```bash
   printf '%s\n' 'video' > export/youtube-upload-target.txt
   printf '%s\n' '萌え更新速報 2026-06-16 18:30' > export/youtube-title.txt
   cat > export/youtube-description.md <<'EOF'
   Codex CLI で作成した更新紹介動画です。
   今回の変更内容が分かるように、動画内にも日時を入れています。
   EOF

   printf '%s\n' '萌え更新速報 Shorts 2026-06-16 18:30 #Shorts' > export/youtube-shorts-title.txt
   cat > export/youtube-shorts-description.md <<'EOF'
   Codex CLI で作成した更新紹介動画の要約Shortsです。
   #Shorts
   EOF
   ```

   `export/youtube-upload-target.txt` は 1 行目だけが使われます。値は `video`、`shorts`、`both` のいずれかです。未作成の場合は `video` です。

   `export/youtube-title.txt` と `export/youtube-shorts-title.txt` は 1 行目だけが title として使われます。`export/youtube-description.md` と `export/youtube-shorts-description.md` は全文が description として使われます。未作成の場合は、アップロード日時入りの値が自動で使われます。

4. 生成した動画を commit します。

   ```bash
   git add -f export/update.mp4
   git add export/youtube-upload-target.txt export/youtube-title.txt export/youtube-description.md
   git commit -m "アップロード用動画を更新"
   ```

   Shorts も対象にする場合は `export/update-shorts.mp4` も追加します。

   ```bash
   git add -f export/update-shorts.mp4
   git add export/youtube-shorts-title.txt export/youtube-shorts-description.md
   ```

   metadata ファイルを作成していない場合、metadata 用の `git add` は不要です。

   jj を使っている場合は、通常の jj の変更として必要な `export/*.mp4` が含まれていることを確認してから commit 説明を付けます。

   ```bash
   jj status
   jj describe -m "アップロード用動画を更新"
   jj bookmark set main -r @
   ```

5. `main` に push します。

   ```bash
   git push origin main
   ```

   jj を使っている場合:

   ```bash
   jj git push --remote origin --bookmark main
   ```

6. GitHub Actions の `YouTube 更新動画の公開` が自動実行されます。
7. 実行結果の `アップロード結果を表示` step または job summary で、アップロード対象の title、video ID、URL を確認します。

Actions は動画ファイルを生成しません。push 済みの `export/update.mp4` または `export/update-shorts.mp4` が存在し、空ファイルでないことを確認してからアップロードします。

Git hook を使う場合は、最初に次を実行します。

```bash
./scripts/install_git_hooks.sh
```

この hook は、`git push` 前にアップロード対象の動画が空ファイルでないこと、サイズが GitHub の通常制限に収まること、未 commit のまま残っていないことを確認します。未 commit の動画がある場合は push を止めるため、動画を commit し忘れたままアップロード workflow だけが走る事故を防げます。

## ローカルでの確認

`ffmpeg` が利用できる環境で、動画生成だけを試せます。

macOS / Linux では次を実行します。

```bash
./scripts/create_sample_video.sh
```

Windows では次を実行します。

```bat
scripts\create_sample_video.bat
```

どちらも `export/update.mp4` に 3 秒のサンプル動画を生成します。

Codex CLI を使い、ChatGPT / Codex に動画生成を依頼する場合は、別の補助スクリプトを使います。

macOS / Linux:

```bash
./scripts/create_video_with_codex.sh
```

Windows:

```bat
scripts\create_video_with_codex.bat
```

このスクリプトは `codex exec` を呼び出し、`scripts/make_video.py` を使わずに ChatGPT / Codex の判断だけで `export/update.mp4` や `export/update-shorts.mp4` を作るよう依頼します。`import/avator.png` が存在する場合は、その画像を主要キャラクター素材として使い、背景、タイトル、装飾、ズーム、パン、フェード、軽い揺れなどの演出を追加して動画化するよう依頼します。`import/*.vrm` や `import/*.unitypackage` が存在する場合も、可能な範囲で利用するよう依頼します。Codex は `ffmpeg` など利用可能なコマンドを選び、動画ファイルを直接生成します。Codex CLI が未インストール、または未ログインの場合は先に Codex CLI のセットアップが必要です。

初期設定では、通常動画だけを横長 16:9 の約 10 秒で作ります。`CODEX_GENERATE_TARGET=shorts` では Shorts 用動画だけ、`CODEX_GENERATE_TARGET=both` では通常動画と Shorts 用動画の両方を作ります。

スクリプトは Codex CLI の実行後に、生成対象に含まれる動画ファイルが存在し、空ファイルではないことを確認します。動画ファイルが作成されなかった場合はエラー終了します。

この方式は Codex CLI の動作確認用です。動画の内容や生成コマンドは Codex の判断に依存するため、毎回まったく同じ結果になるとは限りません。安定した同じ動画を作りたい場合は、通常の `scripts/create_sample_video.sh` / `scripts/create_sample_video.bat` または `scripts/make_video.py` を使ってください。

出力先、タイトル、メッセージ、秒数を変える場合は環境変数を指定します。

```bash
CODEX_VIDEO_OUTPUT="export/codex-update.mp4" \
CODEX_SHORTS_OUTPUT="export/codex-update-shorts.mp4" \
CODEX_IMPORT_IMAGE="import/avator.png" \
CODEX_GENERATE_TARGET="video" \
CODEX_VIDEO_TITLE="萌え更新速報 2026-06-16 17:30" \
CODEX_VIDEO_MESSAGE="ChatGPT / Codex CLI で作成しました。" \
CODEX_VIDEO_DURATION="10" \
CODEX_SHORTS_TITLE="萌え更新速報 Shorts 2026-06-16 17:30 #Shorts" \
CODEX_SHORTS_MESSAGE="通常動画の要約版です。" \
CODEX_SHORTS_DURATION="5" \
CODEX_VIDEO_STYLE="青髪ショートのオリジナル萌え系女子キャラ、星空背景、ウィンク、リボン装飾" \
./scripts/create_video_with_codex.sh
```

直接 `make_video.py` を実行することもできます。

```bash
python3 scripts/make_video.py --output export/update.mp4 --title "Sample Update" --message "Generated by GitHub Actions"
```

`export/update.mp4` が既に存在する場合、`make_video.py` は生成をスキップします。上書きしたい場合は `--force` を付けます。

```bash
python3 scripts/make_video.py --output export/update.mp4 --title "Sample Update" --message "Generated by GitHub Actions" --force
```

`export/update.mp4` と `export/update-shorts.mp4` は YouTube アップロード対象として repository に commit できます。それ以外の `export/*.mp4` は `.gitignore` の対象です。ローカル検証用の別名動画ファイルは repository に commit されません。

アップロードは YouTube 認証情報が必要です。

```bash
YOUTUBE_CLIENT_ID="..." \
YOUTUBE_CLIENT_SECRET="..." \
YOUTUBE_REFRESH_TOKEN="..." \
python3 scripts/upload_youtube.py --file export/update.mp4 --title "Sample Update" --description "Generated by GitHub Actions"
```

アップロードに成功すると、GitHub Actions のログと job summary に通常動画と Shorts の video ID と公開先 URL が表示されます。

## 注意事項

- 初期設定では動画は限定公開としてアップロードされます。
- 公開範囲を変更する場合は、`scripts/upload_youtube.py` の `--privacy-status` または workflow 内の `--privacy-status` を変更してください。
- 通常動画と Shorts を同時アップロードするため、YouTube Data API の quota は 2 本分消費します。
- 実運用では、アップロード頻度、quota、OAuth token の管理、動画タイトルの命名規則をプロジェクトに合わせて調整してください。
