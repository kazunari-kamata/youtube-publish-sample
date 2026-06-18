# youtube-publish-sample

ローカルで作成した短い更新紹介動画と YouTube Shorts 用の要約動画を `main` に push し、GitHub Actions から YouTube Data API で限定公開アップロードするサンプルリポジトリです。

このサンプルは public repository として公開できるように、実在する個人情報、ローカル絶対パス、秘密情報を含めていません。

## できること

- `export/update.mp4` と `export/update-shorts.mp4` を `main` に push した場合は、GitHub Actions が自動で YouTube へアップロード
- GitHub Actions 内では動画を生成せず、push 済みの通常動画と Shorts 用動画だけをアップロード
- アップロード対象は `video`、`shorts`、`both` から選択。未指定時の初期値は `video`
- Blender が使えるローカル端末では `scripts/create_video_with_blender.sh` で `import/*.vrm` を直接読み込んだ動画を生成
- Codex CLI から `scripts/create_video_with_codex.sh` / `scripts/create_video_with_codex.bat` を実行し、ChatGPT / Codex に動画生成を依頼
- GitHub Actions 内で `scripts/upload_youtube.py` を実行し、YouTube Data API に `privacyStatus=unlisted` でアップロード
- YouTube API 認証情報は GitHub Secrets から読み込み
- Google Cloud の VM、Cloud Run、Storage などの有料リソースは使わない

## 使い方

1. Google / YouTube API と GitHub Secrets を設定します。
   詳細: [docs/google-youtube-api.md](docs/google-youtube-api.md)
2. ローカルで動画を生成します。
   詳細: [docs/video-generation.md](docs/video-generation.md)
3. `export/youtube-upload-target.txt` でアップロード対象を選びます。
4. `export/update.mp4` または `export/update-shorts.mp4` を commit して `main` に push します。
5. GitHub Actions の `YouTube 更新動画の公開` でアップロード結果の URL を確認します。
   詳細: [docs/github-actions.md](docs/github-actions.md)

## ドキュメント

| ファイル | 内容 |
| --- | --- |
| [docs/video-generation.md](docs/video-generation.md) | Blender / Codex CLI / ffmpeg での動画生成、commit、push 手順 |
| [docs/github-actions.md](docs/github-actions.md) | workflow の起動条件、アップロード対象、GitHub Secrets |
| [docs/google-youtube-api.md](docs/google-youtube-api.md) | Google Cloud、OAuth、refresh token、複数チャンネル、費用、予算アラート |

## リポジトリ構成

```text
youtube-publish-sample/
├── README.md
├── docs/
│   ├── github-actions.md
│   ├── google-youtube-api.md
│   └── video-generation.md
├── scripts/
│   ├── create_sample_video.bat
│   ├── create_sample_video.sh
│   ├── create_video_with_blender.sh
│   ├── create_video_with_codex.bat
│   ├── create_video_with_codex.sh
│   ├── install_git_hooks.sh
│   ├── make_video.py
│   ├── render_vrm_with_blender.py
│   └── upload_youtube.py
├── import/
│   └── avator.png
├── export/
│   ├── .gitkeep
│   ├── update.mp4
│   ├── update-shorts.mp4
│   └── youtube-upload-target.txt
├── .githooks/
│   └── pre-push
└── .github/
    └── workflows/
        ├── code-check.yml
        └── publish-youtube.yml
```

## クイックチェック

```bash
python -m unittest discover -s tests
```

Blender で通常動画を生成する場合:

```bash
./scripts/create_video_with_blender.sh
```

生成した動画の確認:

```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,nb_frames -of default=noprint_wrappers=1 export/update.mp4
```
