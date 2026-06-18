# GitHub Actions とアップロード設定

## コードチェックとテスト

`.github/workflows/code-check.yml` は、pull request と `main` への push で実行されます。

実行内容:

- Python 3.12 のセットアップ
- `requirements.txt` の依存関係インストール
- `python -m py_compile` による構文チェック
- `python -m unittest discover -s tests` によるテスト

ローカルでも同じテストを実行できます。

```bash
python -m unittest discover -s tests
```

## YouTube アップロードの起動条件

`.github/workflows/publish-youtube.yml` は、`export/update.mp4`、`export/update-shorts.mp4`、`export/youtube-upload-target.txt` の変更を `main` に push した場合に起動します。

README や Python code だけを push しても YouTube アップロードは実行されません。

この workflow は動画生成を行いません。ローカルや Codex CLI で作成して commit 済みの `export/update.mp4` と `export/update-shorts.mp4` を検証し、選択された対象だけを YouTube に限定公開アップロードします。

アップロード対象は次のいずれかです。

| 値 | 動作 |
| --- | --- |
| `video` | `export/update.mp4` だけをアップロードします。初期値です。 |
| `shorts` | `export/update-shorts.mp4` だけをアップロードします。 |
| `both` | 通常動画と Shorts の両方をアップロードします。 |

push で動かす場合は、必要に応じて `export/youtube-upload-target.txt` の 1 行目に `video`、`shorts`、`both` のいずれかを書きます。ファイルが無い場合や空の場合は `video` として扱います。

GitHub Actions の `Run workflow` から手動実行する場合も、同じ `video`、`shorts`、`both` を選べます。

YouTube Shorts には専用のアップロード API endpoint はありません。このサンプルでは、縦長 9:16 の短い動画を通常動画と同じ `videos.insert` でアップロードし、title / description / tag に `#Shorts` や `shorts` を含めます。

YouTube の title / description を指定しない場合、workflow が次のような値を自動で設定します。

```text
Title:
更新動画 2026-06-16 17:50:00 JST

Description:
GitHub Actions からアップロードした更新動画です。

アップロード日時: 2026-06-16 17:50:00 JST
```

Shorts の title / description を指定しない場合も、アップロード日時と `#Shorts` を含む値が自動で設定されます。

## GitHub Secrets

Repository settings の `Secrets and variables` -> `Actions` に、次の secrets を登録してください。

| Secret name | 説明 |
| --- | --- |
| `YOUTUBE_CLIENT_ID` | Google Cloud OAuth client ID |
| `YOUTUBE_CLIENT_SECRET` | Google Cloud OAuth client secret |
| `YOUTUBE_REFRESH_TOKEN` | YouTube Data API 用の OAuth refresh token |

登録手順:

1. GitHub でこの repository を開きます。
2. `Settings` を開きます。
3. 左メニューの `Secrets and variables` -> `Actions` を開きます。
4. `New repository secret` をクリックします。
5. `Name` に secret name を入力します。例: `YOUTUBE_CLIENT_ID`
6. `Secret` に Google Cloud で発行された値を貼り付けます。
7. `Add secret` をクリックします。
8. `YOUTUBE_CLIENT_SECRET` と `YOUTUBE_REFRESH_TOKEN` も同じ手順で登録します。

GitHub Secrets は、workflow 実行時だけ環境変数として読み込まれます。README や workflow ファイルに secret の実値を書かないでください。

複数の YouTube チャンネルへアップロードする場合は、チャンネルごとに refresh token を分けて登録します。

例:

| Secret name | 説明 |
| --- | --- |
| `YOUTUBE_REFRESH_TOKEN_MAIN` | メイン YouTube チャンネル用の refresh token |
| `YOUTUBE_REFRESH_TOKEN_SUB` | サブ YouTube チャンネル用の refresh token |

`YOUTUBE_CLIENT_ID` と `YOUTUBE_CLIENT_SECRET` は、同じ Google Cloud project / OAuth client の値を共通利用できます。どの YouTube チャンネルへアップロードされるかは、`YOUTUBE_REFRESH_TOKEN` を取得するときにログインして認可した Google アカウントで決まります。
