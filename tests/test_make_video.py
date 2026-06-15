from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from scripts.make_video import escape_drawtext, generate_video


class MakeVideoTest(TestCase):
    def test_escape_drawtext_escapes_ffmpeg_special_characters(self) -> None:
        self.assertEqual(
            escape_drawtext("a:b'c%d\\e\nf"),
            "a\\:b\\'c\\%d\\\\e f",
        )

    @patch("scripts.make_video.subprocess.run")
    @patch("scripts.make_video.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_generate_video_invokes_ffmpeg(self, _which, run) -> None:
        generate_video(
            output=Path("output/test.mp4"),
            title="Title",
            message="Message",
            duration=3,
        )

        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("output/test.mp4", command)
        self.assertIn("d=3", command[5])

    @patch("scripts.make_video.shutil.which", return_value=None)
    def test_generate_video_requires_ffmpeg(self, _which) -> None:
        with self.assertRaisesRegex(RuntimeError, "ffmpeg is required"):
            generate_video(
                output=Path("output/test.mp4"),
                title="Title",
                message="Message",
                duration=3,
            )
