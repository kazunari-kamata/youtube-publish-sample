#!/usr/bin/env python3
"""Generate a short update video with ffmpeg."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a short MP4 update video.")
    parser.add_argument("--output", default="output/update.mp4", help="Output MP4 path.")
    parser.add_argument("--title", default="Repository Updated", help="Main title text.")
    parser.add_argument(
        "--message",
        default="A new update was merged to main.",
        help="Secondary message text.",
    )
    parser.add_argument("--duration", type=int, default=8, help="Video duration in seconds.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output video even if it already exists.",
    )
    return parser


def escape_drawtext(value: str) -> str:
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
    if output.exists() and not force:
        print(f"Video already exists, skipping generation: {output}")
        return False

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required but was not found in PATH.")

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
    args = build_parser().parse_args()
    generated = generate_video(
        Path(args.output),
        args.title,
        args.message,
        args.duration,
        force=args.force,
    )
    if generated:
        print(f"Generated video: {args.output}")


if __name__ == "__main__":
    main()
