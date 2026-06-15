# youtube-publish-sample

GitHub の `main` ブランチ更新を契機に、GitHub Actions 上で短い更新紹介動画を生成し、YouTube Data API で限定公開アップロードするサンプルリポジトリです。

このサンプルは public repository として公開できるように、実在する個人情報、ローカル絶対パス、秘密情報を含めていません。

## できること

- `main` への push で GitHub Actions を起動
- GitHub Actions 内で `scripts/make_video.py` を実行し、短い MP4 動画を生成
- GitHub Actions 内で `scripts/upload_youtube.py` を実行し、YouTube Data API にアップロード
- アップロード時の `privacyStatus` は `unlisted`
- YouTube API 認証情報は GitHub Secrets から読み込み
- Google Cloud の VM、Cloud Run、Storage などの有料リソースは使わない

## リポジトリ構成

```text
youtube-publish-sample/
├── README.md
├── scripts/
│   ├── make_video.py
│   └── upload_youtube.py
├── output/
│   └── .gitkeep
└── .github/
    └── workflows/
        └── publish-youtube.yml
```

## GitHub Secrets

Repository settings の `Secrets and variables` -> `Actions` に、次の secrets を登録してください。

| Secret name | 説明 |
| --- | --- |
| `YOUTUBE_CLIENT_ID` | Google Cloud OAuth client ID |
| `YOUTUBE_CLIENT_SECRET` | Google Cloud OAuth client secret |
| `YOUTUBE_REFRESH_TOKEN` | YouTube Data API 用の OAuth refresh token |

## 無料前提の YouTube API 設定

このサンプルは GitHub Actions 上で動画生成とアップロードを実行します。Google Cloud 上でサーバーやストレージを作成する必要はありません。

ただし、YouTube へのアップロードには Google の OAuth 認可が必要です。そのため、無料の API/OAuth 設定として次の作業だけ行います。

1. Google Cloud Console または Google API Console で API 用プロジェクトを作成します。
2. 課金リソースは作成せず、YouTube Data API v3 だけを有効化します。
3. OAuth consent screen を設定します。
4. OAuth client を作成します。
5. `https://www.googleapis.com/auth/youtube.upload` scope を使って refresh token を発行します。
6. 発行した値を GitHub Secrets に登録します。

初回の OAuth 同意だけはブラウザでの手動認可が必要です。GitHub Actions はブラウザで Google アカウントにログインできないため、初回認可まで完全自動化する構成にはしていません。認可後は、`main` への push ごとに GitHub Actions が動画生成から YouTube への限定公開アップロードまで実行します。

## Google 側の設定手順

Google Cloud project は、YouTube API を使うための設定入れ物です。VM、Cloud Run、Storage などの実行環境を作る必要はありません。

### 1. API 用 project を作成する

1. [Google Cloud Console](https://console.cloud.google.com/) を開きます。
2. Google アカウントでログインします。
3. 画面上部の project 選択プルダウンを開きます。
4. `新しいプロジェクト` をクリックします。
5. Project name に `youtube-publish-sample` などを入力します。
6. `作成` をクリックします。

### 2. YouTube Data API v3 を有効化する

1. [API Library](https://console.cloud.google.com/apis/library) を開きます。
2. 画面上部で、先ほど作成した project が選択されていることを確認します。
3. 検索欄に `YouTube Data API v3` と入力します。
4. `YouTube Data API v3` をクリックします。
5. `有効にする` をクリックします。

### 3. OAuth consent screen を設定する

OAuth consent screen は、Google ログイン時に表示される「このアプリに YouTube アップロード権限を許可しますか？」という確認画面の設定です。

1. [Google Auth Platform](https://console.cloud.google.com/auth/overview) を開きます。
2. 画面上部で対象 project が選択されていることを確認します。
3. `Get started` または `OAuth consent screen` を開きます。
4. App name に `youtube-publish-sample` などを入力します。
5. User support email に自分の Google アカウントを選択します。
6. Audience または User type は、個人利用なら `External` を選択します。
7. Contact email に自分のメールアドレスを入力します。
8. Scopes に `https://www.googleapis.com/auth/youtube.upload` を追加します。
9. Test users に、アップロード先 YouTube チャンネルを持つ自分の Google アカウントを追加します。
10. 保存します。

一般公開しない OAuth app でも、Test users に自分を追加すれば、自分のアカウントで認可できます。

### 4. OAuth client を作成する

OAuth client は、GitHub Actions から YouTube API を使うための `client_id` と `client_secret` を発行する設定です。

1. [Google Auth Platform Clients](https://console.cloud.google.com/auth/clients) を開きます。
2. `CREATE CLIENT` または `クライアントを作成` をクリックします。
3. Application type は `Desktop app` を選択します。
4. Name に `youtube-publish-sample-local` などを入力します。
5. `Create` をクリックします。
6. 表示された Client ID を GitHub Secrets の `YOUTUBE_CLIENT_ID` に登録します。
7. 表示された Client secret を GitHub Secrets の `YOUTUBE_CLIENT_SECRET` に登録します。

`YOUTUBE_REFRESH_TOKEN` は、この OAuth client を使って一度だけブラウザで YouTube アップロード権限を許可した後に取得する値です。

参考:

- [YouTube Data API Python Quickstart](https://developers.google.com/youtube/v3/quickstart/python)
- [Manage OAuth Clients](https://support.google.com/cloud/answer/15549257)

## 費用について

このサンプルが使う処理は次の通りです。

- 動画生成: GitHub Actions の runner 上で実行
- YouTube アップロード: YouTube Data API v3 を利用
- Google Cloud 有料リソース: 未使用

public repository であれば GitHub Actions の利用枠は無料で使えます。YouTube Data API は quota 制で、通常の少量アップロードであれば追加費用なしで試せます。Google Cloud の VM、Cloud Run、Cloud Storage、BigQuery などを作成しないでください。

YouTube Data API のデフォルト quota は次の通りです。

- `videos.insert`: 100 回/日
- `search.list`: 100 回/日
- その他の endpoint: 合計 10,000 units/日
- quota は Pacific Time の午前 0 時にリセット
- 無効な API request でも最低 1 quota point を消費

このサンプルの upload 処理は `videos.insert` を 1 回呼び出します。そのため、単純計算では 1 project あたり 1 日 100 本までのアップロードがデフォルト quota の目安です。

## 予算アラートの設定

このサンプルでは Google Cloud の有料リソースを使いませんが、誤って VM、Cloud Run、Cloud Storage などを作成した場合に気づけるよう、予算アラートを設定しておくと安心です。

予算アラートは「設定金額に近づいたらメールで通知する」機能です。課金を自動停止する機能ではありません。

1. [Google Cloud Billing Budgets](https://console.cloud.google.com/billing/budgets) を開きます。
2. 対象の billing account を選択します。
3. `Create budget` または `予算を作成` をクリックします。
4. Name に `youtube-publish-sample-budget` などを入力します。
5. Scope で、このサンプル用の project だけを対象にします。
6. Amount は少額にします。例: `100 JPY` または `1 USD`
7. Alerts は `50%`, `90%`, `100%` などを設定します。
8. 通知先メールを確認して保存します。

この設定をしても、YouTube Data API の無料 quota が増減するわけではありません。あくまで Google Cloud 側で想定外の課金リソースを作ってしまった場合に気づくための保険です。

## API を使わない自動操作について

MCP、Playwright、Chrome 自動操作などで YouTube Studio の画面を操作してアップロードする方法は、技術的には実装できる場合があります。

ただし、YouTube の Terms of Service では、YouTube の事前許可なしに bot、scraper などの automated means で Service にアクセスすることが制限されています。そのため、このリポジトリでは YouTube Studio のブラウザ自動操作によるアップロードは採用せず、公式に提供されている YouTube Data API を使います。

安全のため、Google Cloud Console で billing budget や予算アラートを設定しておくと安心です。

## ローカルでの確認

`ffmpeg` が利用できる環境で、動画生成だけを試せます。

```bash
python3 scripts/make_video.py --output output/update.mp4 --title "Sample Update" --message "Generated by GitHub Actions"
```

アップロードは YouTube 認証情報が必要です。

```bash
YOUTUBE_CLIENT_ID="..." \
YOUTUBE_CLIENT_SECRET="..." \
YOUTUBE_REFRESH_TOKEN="..." \
python3 scripts/upload_youtube.py --file output/update.mp4 --title "Sample Update" --description "Generated by GitHub Actions"
```

## 注意事項

- 初期設定では動画は限定公開としてアップロードされます。
- 公開範囲を変更する場合は、`scripts/upload_youtube.py` の `--privacy-status` または workflow の引数を変更してください。
- 実運用では、アップロード頻度、quota、OAuth token の管理、動画タイトルの命名規則をプロジェクトに合わせて調整してください。
