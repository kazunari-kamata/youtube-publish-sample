#!/usr/bin/env python3
"""環境変数の認証情報を使って動画を YouTube にアップロードします。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def build_parser() -> argparse.ArgumentParser:
    """YouTube アップロードコマンドの引数パーサーを作成します。"""

    parser = argparse.ArgumentParser(description="動画を YouTube にアップロードします。")
    parser.add_argument("--file", required=True, help="アップロードする MP4 ファイルのパス。")
    parser.add_argument("--title", required=True, help="YouTube 動画タイトル。")
    parser.add_argument("--description", default="", help="YouTube 動画説明文。")
    parser.add_argument("--tags", default="", help="カンマ区切りの YouTube タグ。")
    parser.add_argument(
        "--privacy-status",
        default="unlisted",
        choices=["private", "unlisted", "public"],
        help="YouTube の公開範囲。",
    )
    return parser


def require_env(name: str) -> str:
    """必須の環境変数を取得し、未設定なら分かりやすいエラーを出します。"""

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"必須の環境変数が未設定です: {name}")
    return value


def youtube_client():
    """認証済みの YouTube Data API client を作成します。"""

    credentials = Credentials(
        token=None,
        refresh_token=require_env("YOUTUBE_REFRESH_TOKEN"),
        token_uri=TOKEN_URI,
        client_id=require_env("YOUTUBE_CLIENT_ID"),
        client_secret=require_env("YOUTUBE_CLIENT_SECRET"),
        scopes=[YOUTUBE_UPLOAD_SCOPE],
    )
    return build("youtube", "v3", credentials=credentials)


def upload_video(
    file_path: Path,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str,
) -> str:
    """動画ファイルを YouTube にアップロードし、アップロード後の video ID を返します。"""

    if not file_path.exists():
        raise FileNotFoundError(f"動画ファイルが存在しません: {file_path}")

    youtube = youtube_client()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }
    media = MediaFileUpload(str(file_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"アップロード進行状況: {int(status.progress() * 100)}%")

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"アップロードした動画: {video_url}")
    return video_id


def main() -> None:
    """コマンドラインから YouTube アップロード処理を実行します。"""

    args = build_parser().parse_args()
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

    try:
        video_id = upload_video(
            file_path=Path(args.file),
            title=args.title,
            description=args.description,
            tags=tags,
            privacy_status=args.privacy_status,
        )
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as output:
                output.write(f"video_id={video_id}\n")
                output.write(f"video_url={video_url}\n")
    except HttpError as error:
        raise RuntimeError(f"YouTube API アップロードに失敗しました: {error}") from error


if __name__ == "__main__":
    main()
