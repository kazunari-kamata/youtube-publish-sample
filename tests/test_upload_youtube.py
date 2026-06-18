import os
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


class _FakeCredentials:
    """google.oauth2.credentials.Credentials の最小スタブです。"""

    def __init__(self, **_kwargs) -> None:
        """本テストでは認証情報の中身を検証しないため何もしません。"""

        pass


class _FakeHttpError(Exception):
    """googleapiclient.errors.HttpError の代替例外です。"""

    pass


def _install_google_api_stubs() -> None:
    """google-api-python-client 未インストール環境でも import できるようにします。"""

    google = types.ModuleType("google")
    oauth2 = types.ModuleType("google.oauth2")
    credentials = types.ModuleType("google.oauth2.credentials")
    googleapiclient = types.ModuleType("googleapiclient")
    discovery = types.ModuleType("googleapiclient.discovery")
    errors = types.ModuleType("googleapiclient.errors")
    http = types.ModuleType("googleapiclient.http")

    credentials.Credentials = _FakeCredentials
    discovery.build = lambda *_args, **_kwargs: None
    errors.HttpError = _FakeHttpError
    http.MediaFileUpload = lambda *_args, **_kwargs: None

    sys.modules.setdefault("google", google)
    sys.modules.setdefault("google.oauth2", oauth2)
    sys.modules.setdefault("google.oauth2.credentials", credentials)
    sys.modules.setdefault("googleapiclient", googleapiclient)
    sys.modules.setdefault("googleapiclient.discovery", discovery)
    sys.modules.setdefault("googleapiclient.errors", errors)
    sys.modules.setdefault("googleapiclient.http", http)


_install_google_api_stubs()

from scripts import upload_youtube


class _FakeUploadStatus:
    """resumable upload の進捗オブジェクトを模したスタブです。"""

    def progress(self) -> float:
        """アップロード完了を表す 100% の進捗を返します。"""

        return 1.0


class _FakeInsertRequest:
    """YouTube videos.insert の request object を模したスタブです。"""

    def __init__(self) -> None:
        """next_chunk 呼び出し回数を初期化します。"""

        self.calls = 0

    def next_chunk(self):
        """1回の呼び出しでアップロード完了レスポンスを返します。"""

        self.calls += 1
        return _FakeUploadStatus(), {"id": "abc123"}


class _FakeVideosResource:
    """YouTube API の videos resource を模したスタブです。"""

    def __init__(self) -> None:
        """insert の引数と返却 request を保持します。"""

        self.insert_kwargs = None
        self.request = _FakeInsertRequest()

    def insert(self, **kwargs):
        """upload_video が組み立てた insert 引数を保存します。"""

        self.insert_kwargs = kwargs
        return self.request


class _FakeYouTubeClient:
    """YouTube API client の最小スタブです。"""

    def __init__(self) -> None:
        """videos resource を初期化します。"""

        self.videos_resource = _FakeVideosResource()

    def videos(self) -> _FakeVideosResource:
        """videos resource を返します。"""

        return self.videos_resource


class UploadYouTubeTest(TestCase):
    """YouTube アップロード処理の単体テストです。"""

    def test_require_env_returns_value(self) -> None:
        """必須環境変数が設定済みなら値を返すことを確認します。"""

        with patch.dict(os.environ, {"EXAMPLE_SECRET": "value"}):
            self.assertEqual(upload_youtube.require_env("EXAMPLE_SECRET"), "value")

    def test_require_env_rejects_missing_value(self) -> None:
        """必須環境変数が未設定なら RuntimeError になることを確認します。"""

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "必須の環境変数"):
                upload_youtube.require_env("EXAMPLE_SECRET")

    def test_upload_video_returns_video_id_and_builds_request(self) -> None:
        """動画 ID が返り、YouTube API request body が期待通り作られることを確認します。"""

        client = _FakeYouTubeClient()

        with TemporaryDirectory() as tmpdir:
            video = Path(tmpdir) / "video.mp4"
            video.write_bytes(b"fake mp4")

            with (
                patch.object(upload_youtube, "youtube_client", return_value=client),
                patch.object(upload_youtube, "MediaFileUpload", return_value="media"),
            ):
                video_id = upload_youtube.upload_video(
                    file_path=video,
                    title="Title",
                    description="Description",
                    tags=["tag1", "tag2"],
                    privacy_status="unlisted",
                )

        self.assertEqual(video_id, "abc123")
        insert_kwargs = client.videos_resource.insert_kwargs
        self.assertEqual(insert_kwargs["part"], "snippet,status")
        self.assertEqual(insert_kwargs["media_body"], "media")
        self.assertEqual(insert_kwargs["body"]["snippet"]["title"], "Title")
        self.assertEqual(insert_kwargs["body"]["snippet"]["tags"], ["tag1", "tag2"])
        self.assertEqual(insert_kwargs["body"]["status"]["privacyStatus"], "unlisted")

    def test_upload_video_requires_existing_file(self) -> None:
        """アップロード対象ファイルが無い場合は FileNotFoundError になることを確認します。"""

        with self.assertRaises(FileNotFoundError):
            upload_youtube.upload_video(
                file_path=Path("missing.mp4"),
                title="Title",
                description="Description",
                tags=[],
                privacy_status="unlisted",
            )
