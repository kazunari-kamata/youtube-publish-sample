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

1. <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer">Google Cloud Console</a> を開きます。
2. Google アカウントでログインします。
3. 画面上部の project 選択プルダウンを開きます。
4. `新しいプロジェクト` をクリックします。
5. Project name に `youtube-publish-sample` などを入力します。
6. `作成` をクリックします。

### 2. YouTube Data API v3 を有効化する

1. <a href="https://console.cloud.google.com/apis/library" target="_blank" rel="noopener noreferrer">API Library</a> を開きます。
2. 画面上部で、先ほど作成した project が選択されていることを確認します。
3. 検索欄に `YouTube Data API v3` と入力します。
4. `YouTube Data API v3` をクリックします。
5. `有効にする` をクリックします。

### 3. OAuth consent screen を設定する

OAuth consent screen は、Google ログイン時に表示される「このアプリに YouTube アップロード権限を許可しますか？」という確認画面の設定です。

1. <a href="https://console.cloud.google.com/auth/overview" target="_blank" rel="noopener noreferrer">Google Auth Platform</a> を開きます。
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

1. <a href="https://console.cloud.google.com/auth/clients" target="_blank" rel="noopener noreferrer">Google Auth Platform Clients</a> を開きます。
2. `CREATE CLIENT` または `クライアントを作成` をクリックします。
3. Application type は `Desktop app` を選択します。
4. Name に `youtube-publish-sample-local` などを入力します。
5. `Create` をクリックします。
6. 画面に `Client ID` と `Client secret` が表示されます。
7. `Client ID` の値をコピーします。
8. `Client secret` の値をコピーします。
9. GitHub repository の `Settings` -> `Secrets and variables` -> `Actions` を開きます。
10. `New repository secret` をクリックします。
11. `Name` に `YOUTUBE_CLIENT_ID` と入力します。
12. `Secret` に Google Cloud の `Client ID` を貼り付けます。
13. `Add secret` をクリックします。
14. もう一度 `New repository secret` をクリックします。
15. `Name` に `YOUTUBE_CLIENT_SECRET` と入力します。
16. `Secret` に Google Cloud の `Client secret` を貼り付けます。
17. `Add secret` をクリックします。

`Client secret` の場所が分からない場合は、次のどちらかで確認できます。

- OAuth client 作成直後: `Client created` のようなポップアップに `Client ID` と `Client secret` が表示されます。
- 後から確認する場合: <a href="https://console.cloud.google.com/auth/clients" target="_blank" rel="noopener noreferrer">Google Auth Platform Clients</a> を開き、作成した client name、例: `youtube-publish-sample-local` をクリックします。詳細画面の `Client secret` 欄に表示されます。

Google Cloud の `Client secret` は、GitHub の secret 登録画面の `Secret` 入力欄に貼り付けます。`Name` 入力欄には secret の名前、つまり `YOUTUBE_CLIENT_SECRET` を入力します。

`YOUTUBE_REFRESH_TOKEN` は、この OAuth client を使って一度だけブラウザで YouTube アップロード権限を許可した後に取得する値です。

参考:

- <a href="https://developers.google.com/youtube/v3/quickstart/python" target="_blank" rel="noopener noreferrer">YouTube Data API Python Quickstart</a>
- <a href="https://support.google.com/cloud/answer/15549257" target="_blank" rel="noopener noreferrer">Manage OAuth Clients</a>

## Google アカウントと YouTube チャンネル

Google Cloud project を作る Google アカウントと、アップロード先 YouTube チャンネルを持つ Google アカウントは同一でなくても構いません。

役割は次のように分かれます。

- Google Cloud 側アカウント: API project、YouTube Data API v3、OAuth client を管理する
- YouTube 側アカウント: OAuth 同意を行い、refresh token を発行する
- GitHub Actions: refresh token に紐づく YouTube チャンネルへ動画をアップロードする

OAuth consent screen の Test users には、実際に OAuth 同意を行う YouTube 側の Google アカウントを追加してください。

## 複数 YouTube チャンネルに対応する場合

複数チャンネルに対応する場合は、チャンネルごとに `YOUTUBE_REFRESH_TOKEN` を発行して GitHub Secrets に登録します。

考え方:

- `YOUTUBE_CLIENT_ID`: Google Cloud の OAuth client。複数チャンネルで共通利用できます。
- `YOUTUBE_CLIENT_SECRET`: Google Cloud の OAuth client secret。複数チャンネルで共通利用できます。
- `YOUTUBE_REFRESH_TOKEN`: YouTube チャンネルごとに別々に用意します。

例:

| アップロード先 | GitHub Secret name |
| --- | --- |
| メインチャンネル | `YOUTUBE_REFRESH_TOKEN_MAIN` |
| サブチャンネル | `YOUTUBE_REFRESH_TOKEN_SUB` |
| 会社用チャンネル | `YOUTUBE_REFRESH_TOKEN_COMPANY` |

どのチャンネルにアップロードされるかは、OAuth 同意時に選択した YouTube チャンネルと、そのとき発行された refresh token で決まります。

### 同じ Google アカウントが複数チャンネルを管理している場合

例として、同じ Google アカウントが「メインチャンネル」と「サブチャンネル」を管理している場合です。

ここでいう Google ログイン画面は、refresh token を取得するために OAuth 認可 URL をブラウザで開いたときに表示される Google のログイン画面です。GitHub Actions の画面ではありません。

1. refresh token 取得用の手順を開始し、OAuth 認可 URL をブラウザで開きます。
2. ブラウザに Google のログイン画面が表示されたら、YouTube チャンネルを管理している Google アカウントでログインします。
3. Google から「どの YouTube チャンネルで続行しますか？」のような選択画面が出た場合、まずメインチャンネルを選択します。
4. YouTube アップロード権限を許可します。
5. メインチャンネル用の refresh token を取得します。
6. GitHub repository の `Settings` -> `Secrets and variables` -> `Actions` を開きます。
7. `New repository secret` をクリックします。
8. `Name` に `YOUTUBE_REFRESH_TOKEN_MAIN` と入力します。
9. `Secret` にメインチャンネル用 refresh token を貼り付けます。
10. `Add secret` をクリックします。
11. 次に、もう一度 refresh token 取得用の手順を開始し、OAuth 認可 URL をブラウザで開きます。
12. ブラウザに Google のログイン画面が表示されたら、同じ Google アカウントでログインします。
13. チャンネル選択画面で、今度はサブチャンネルを選択します。
14. YouTube アップロード権限を許可します。
15. サブチャンネル用の refresh token を取得します。
16. GitHub Secrets に `YOUTUBE_REFRESH_TOKEN_SUB` という名前で登録します。

### Google アカウント自体がチャンネルごとに異なる場合

例として、メインチャンネルは `main@example.com`、サブチャンネルは `sub@example.com` が管理している場合です。

1. <a href="https://console.cloud.google.com/auth/overview" target="_blank" rel="noopener noreferrer">Google Auth Platform</a> を開きます。
2. OAuth consent screen の Test users に `main@example.com` を追加します。
3. 同じ Test users に `sub@example.com` も追加します。
4. refresh token 取得用の手順を開始し、OAuth 認可 URL をブラウザで開きます。
5. ブラウザに Google のログイン画面が表示されたら、メインチャンネルを管理している Google アカウントでログインします。`main@example.com` は例なので、実際には自分の Google アカウントを使います。
6. YouTube アップロード権限を許可します。
7. メインチャンネル用 refresh token を取得します。
8. GitHub Secrets に `YOUTUBE_REFRESH_TOKEN_MAIN` として登録します。
9. もう一度 refresh token 取得用の手順を開始し、OAuth 認可 URL をブラウザで開きます。
10. ブラウザに Google のログイン画面が表示されたら、サブチャンネルを管理している Google アカウントでログインします。`sub@example.com` は例なので、実際には自分の Google アカウントを使います。
11. YouTube アップロード権限を許可します。
12. サブチャンネル用 refresh token を取得します。
13. GitHub Secrets に `YOUTUBE_REFRESH_TOKEN_SUB` として登録します。

OAuth consent screen の Test users に追加していない Google アカウントでは、未公開の OAuth app を認可できない場合があります。

### GitHub Secrets の登録例

複数チャンネル運用では、最低限次のように登録します。

| Secret name | 入れる値 |
| --- | --- |
| `YOUTUBE_CLIENT_ID` | Google Cloud の Client ID |
| `YOUTUBE_CLIENT_SECRET` | Google Cloud の Client secret |
| `YOUTUBE_REFRESH_TOKEN_MAIN` | メインチャンネルで OAuth 同意して取得した refresh token |
| `YOUTUBE_REFRESH_TOKEN_SUB` | サブチャンネルで OAuth 同意して取得した refresh token |

### workflow でチャンネルを切り替える例

このサンプルの workflow は単一チャンネル用です。複数チャンネルで使う場合は、upload step の `YOUTUBE_REFRESH_TOKEN` に渡す secret を切り替えます。

```yaml
env:
  YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
  YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
  YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN_MAIN }}
```

サブチャンネルへアップロードしたい workflow では、次のように変更します。

```yaml
env:
  YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
  YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
  YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN_SUB }}
```

同じ GitHub Actions run で複数チャンネルへ同時にアップロードする場合は、upload step をチャンネル数分だけ追加し、それぞれ別の refresh token secret を渡してください。

例:

```yaml
- name: メインチャンネルへアップロード
  env:
    YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
    YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
    YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN_MAIN }}
  run: |
    python scripts/upload_youtube.py \
      --file output/update.mp4 \
      --title "main ブランチ更新のお知らせ" \
      --description "メインチャンネル向けの更新動画です。" \
      --privacy-status unlisted

- name: サブチャンネルへアップロード
  env:
    YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
    YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
    YOUTUBE_REFRESH_TOKEN: ${{ secrets.YOUTUBE_REFRESH_TOKEN_SUB }}
  run: |
    python scripts/upload_youtube.py \
      --file output/update.mp4 \
      --title "main ブランチ更新のお知らせ" \
      --description "サブチャンネル向けの更新動画です。" \
      --privacy-status unlisted
```

この場合、同じ動画ファイルを 2 つの YouTube チャンネルへそれぞれ 1 回ずつアップロードします。YouTube Data API の quota も 2 回分消費します。

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

1. <a href="https://console.cloud.google.com/billing/budgets" target="_blank" rel="noopener noreferrer">Google Cloud Billing Budgets</a> を開きます。
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
