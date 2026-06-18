from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts.make_video import escape_drawtext, generate_video
from scripts.render_vrm_with_blender import count_unity_assets, find_first_file, resolve_path


class MakeVideoTest(TestCase):
    """動画生成と Blender 補助関数の単体テストです。"""

    def test_escape_drawtext_escapes_ffmpeg_special_characters(self) -> None:
        """ffmpeg drawtext で意味を持つ文字がエスケープされることを確認します。"""

        self.assertEqual(
            escape_drawtext("a:b'c%d\\e\nf"),
            "a\\:b\\'c\\%d\\\\e f",
        )

    @patch("scripts.make_video.subprocess.run")
    @patch("scripts.make_video.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_generate_video_invokes_ffmpeg(self, _which, run) -> None:
        """ffmpeg が存在する場合に動画生成コマンドが実行されることを確認します。"""

        generated = generate_video(
            output=Path("export/test.mp4"),
            title="Title",
            message="Message",
            duration=3,
        )

        self.assertTrue(generated)
        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("export/test.mp4", command)
        self.assertIn("d=3", command[5])

    @patch("scripts.make_video.shutil.which", return_value=None)
    def test_generate_video_requires_ffmpeg(self, _which) -> None:
        """ffmpeg が PATH に無い場合は分かりやすい例外になることを確認します。"""

        with self.assertRaisesRegex(RuntimeError, "ffmpeg が必要"):
            generate_video(
                output=Path("export/test.mp4"),
                title="Title",
                message="Message",
                duration=3,
            )

    @patch("scripts.make_video.subprocess.run")
    @patch("scripts.make_video.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_generate_video_skips_existing_file_without_force(self, _which, run) -> None:
        """既存動画があり force 無効の場合は生成をスキップすることを確認します。"""

        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "existing.mp4"
            output.write_bytes(b"already exists")

            generated = generate_video(
                output=output,
                title="Title",
                message="Message",
                duration=3,
            )

        self.assertFalse(generated)
        run.assert_not_called()

    @patch("scripts.make_video.subprocess.run")
    @patch("scripts.make_video.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_generate_video_overwrites_existing_file_with_force(self, _which, run) -> None:
        """既存動画があっても force 有効なら再生成することを確認します。"""

        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "existing.mp4"
            output.write_bytes(b"already exists")

            generated = generate_video(
                output=output,
                title="Title",
                message="Message",
                duration=3,
                force=True,
            )

        self.assertTrue(generated)
        run.assert_called_once()

    def test_resolve_path_uses_repo_root_for_relative_path(self) -> None:
        """相対パスが repository root 基準の絶対パスに解決されることを確認します。"""

        repo_root = Path("/repo")

        self.assertEqual(resolve_path(repo_root, "export/update.mp4"), Path("/repo/export/update.mp4"))

    def test_find_first_file_returns_sorted_match(self) -> None:
        """複数ファイルがある場合に名前順で最初の一致を返すことを確認します。"""

        with TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            (directory / "b.vrm").write_text("b", encoding="utf-8")
            (directory / "a.vrm").write_text("a", encoding="utf-8")

            self.assertEqual(find_first_file(directory, "*.vrm"), directory / "a.vrm")

    def test_count_unity_assets_counts_asset_entries(self) -> None:
        """unitypackage 内の asset エントリ数を数えられることを確認します。"""

        with TemporaryDirectory() as tmpdir:
            package = Path(tmpdir) / "sample.unitypackage"
            asset_dir = Path(tmpdir) / "payload" / "abc"
            asset_dir.mkdir(parents=True)
            (asset_dir / "asset").write_text("asset", encoding="utf-8")
            (asset_dir / "pathname").write_text("Assets/Sample.asset", encoding="utf-8")

            with tarfile.open(package, "w:gz") as archive:
                archive.add(asset_dir, arcname="abc")

            self.assertEqual(count_unity_assets(package), 1)
