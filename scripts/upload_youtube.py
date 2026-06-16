#!/usr/bin/env python3
"""Upload a video to YouTube using credentials from environment variables."""

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
    """Build the command-line argument parser for YouTube uploads."""

    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("--file", required=True, help="Path to the MP4 file to upload.")
    parser.add_argument("--title", required=True, help="YouTube video title.")
    parser.add_argument("--description", default="", help="YouTube video description.")
    parser.add_argument("--tags", default="", help="Comma-separated YouTube tags.")
    parser.add_argument(
        "--privacy-status",
        default="unlisted",
        choices=["private", "unlisted", "public"],
        help="YouTube privacy status.",
    )
    return parser


def require_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def youtube_client():
    """Create an authenticated YouTube Data API client."""

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
    """Upload a video file to YouTube and return the uploaded video ID."""

    if not file_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {file_path}")

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
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Uploaded video: {video_url}")
    return video_id


def main() -> None:
    """Run the command-line YouTube upload flow."""

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
        raise RuntimeError(f"YouTube API upload failed: {error}") from error


if __name__ == "__main__":
    main()
