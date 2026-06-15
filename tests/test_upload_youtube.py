import os
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


class _FakeCredentials:
    def __init__(self, **_kwargs) -> None:
        pass


class _FakeHttpError(Exception):
    pass


def _install_google_api_stubs() -> None:
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
    def progress(self) -> float:
        return 1.0


class _FakeInsertRequest:
    def __init__(self) -> None:
        self.calls = 0

    def next_chunk(self):
        self.calls += 1
        return _FakeUploadStatus(), {"id": "abc123"}


class _FakeVideosResource:
    def __init__(self) -> None:
        self.insert_kwargs = None
        self.request = _FakeInsertRequest()

    def insert(self, **kwargs):
        self.insert_kwargs = kwargs
        return self.request


class _FakeYouTubeClient:
    def __init__(self) -> None:
        self.videos_resource = _FakeVideosResource()

    def videos(self) -> _FakeVideosResource:
        return self.videos_resource


class UploadYouTubeTest(TestCase):
    def test_require_env_returns_value(self) -> None:
        with patch.dict(os.environ, {"EXAMPLE_SECRET": "value"}):
            self.assertEqual(upload_youtube.require_env("EXAMPLE_SECRET"), "value")

    def test_require_env_rejects_missing_value(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Missing required environment variable"):
                upload_youtube.require_env("EXAMPLE_SECRET")

    def test_upload_video_returns_video_id_and_builds_request(self) -> None:
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
        with self.assertRaises(FileNotFoundError):
            upload_youtube.upload_video(
                file_path=Path("missing.mp4"),
                title="Title",
                description="Description",
                tags=[],
                privacy_status="unlisted",
            )
