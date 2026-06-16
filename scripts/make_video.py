#!/usr/bin/env python3
"""ffmpeg で短い更新紹介動画を生成します。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """動画生成コマンドの引数パーサーを作成します。"""

    parser = argparse.ArgumentParser(description="短い MP4 更新紹介動画を生成します。")
    parser.add_argument("--output", default="output/update.mp4", help="出力する MP4 ファイルのパス。")
    parser.add_argument("--title", default="Repository Updated", help="動画に表示するタイトル。")
    parser.add_argument(
        "--message",
        default="A new update was merged to main.",
        help="動画に表示する補足メッセージ。",
    )
    parser.add_argument("--duration", type=int, default=8, help="動画の秒数。")
    parser.add_argument(
        "--force",
        action="store_true",
        help="出力先の動画が既に存在しても上書きします。",
    )
    return parser


def escape_drawtext(value: str) -> str:
    """ffmpeg の drawtext filter で使う文字列をエスケープします。"""

    return (
        value.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
        .replace("\n", " ")
    )


def generate_video(
    output: Path,
    title: str,
    message: str,
    duration: int,
    force: bool = False,
) -> bool:
    """出力先に動画が存在しない場合だけ MP4 動画を生成します。

    新しく動画を生成した場合は True を返します。既存ファイルがあり、
    force が無効なため生成をスキップした場合は False を返します。
    """

    if output.exists() and not force:
        print(f"動画が既に存在するため生成をスキップします: {output}")
        return False

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg が必要ですが PATH に見つかりません。")

    output.parent.mkdir(parents=True, exist_ok=True)

    title_text = escape_drawtext(title)
    message_text = escape_drawtext(message)
    filter_graph = (
        "color=c=0x102033:s=1280x720:d={duration},format=yuv420p,"
        "drawbox=x=0:y=0:w=1280:h=720:color=0x102033@1:t=fill,"
        "drawbox=x=80:y=92:w=1120:h=536:color=0x1d6f78@0.25:t=fill,"
        "drawtext=text='{title}':fontcolor=white:fontsize=64:"
        "x=(w-text_w)/2:y=250,"
        "drawtext=text='{message}':fontcolor=0xd8f3f0:fontsize=34:"
        "x=(w-text_w)/2:y=360,"
        "drawtext=text='Generated from GitHub Actions':fontcolor=0xaed8d3:"
        "fontsize=24:x=(w-text_w)/2:y=500"
    ).format(duration=duration, title=title_text, message=message_text)

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        filter_graph,
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(command, check=True)
    return True


def main() -> None:
    """コマンドラインから動画生成処理を実行します。"""

    args = build_parser().parse_args()
    generated = generate_video(
        Path(args.output),
        args.title,
        args.message,
        args.duration,
        force=args.force,
    )
    if generated:
        print(f"動画を生成しました: {args.output}")


if __name__ == "__main__":
    main()
