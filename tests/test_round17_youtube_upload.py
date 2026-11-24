"""Vòng 17 (PR-15): kiểm tra YouTube Auto-Upload Draft (`vidlib/ytupload.py`) không cần gọi API thật."""
import json
import os
import tempfile
import unittest
from unittest import mock

from vidlib import ytupload
from vidlib.common import StudioError


def _sample_sb(slug="strawberry-r-count"):
    return {
        "slug": slug,
        "topic": "Why AI can't count the R's in strawberry",
        "title": "Why AI Fails Counting R's",
        "language": "en",
        "publish": {
            "youtube_shorts": {
                "titles": [
                    "Why AI Can't Count the R's in Strawberry",
                    "The Weird Reason AI Fails This 2-Second Test",
                    "AI Doesn't Read Letters — Here's Why",
                ],
                "description": (
                    "Ask an LLM how many R's are in strawberry and it often says two. "
                    "Tokenizers slice words into chunks instead of individual letters."
                ),
                "hashtags": ["ai", "tech", "shorts"],
                "tags": ["ai tokenization", "strawberry test", "llm explained", "science shorts"],
                "pinned_comment": "Try asking your AI how many R's are in 'raspberry' — what did it say?",
            }
        },
        "shots": [],
    }


def _make_fake_youtube(video_id="yt12345abc", fail_captions=False):
    calls = {"videos": [], "captions": [], "comments": []}

    class _FakeStatus:
        def __init__(self, p):
            self._p = p

        def progress(self):
            return self._p

    class _FakeVideoReq:
        def __init__(self):
            self._step = 0

        def next_chunk(self):
            self._step += 1
            if self._step == 1:
                return _FakeStatus(0.5), None
            return None, {"id": video_id}

    class _FakeExec:
        def __init__(self, fail=False):
            self._fail = fail

        def execute(self):
            if self._fail:
                raise RuntimeError("caption scope error")
            return {"ok": True}

    class _FakeVideos:
        def insert(self, **kwargs):
            calls["videos"].append(kwargs)
            return _FakeVideoReq()

    class _FakeCaptions:
        def insert(self, **kwargs):
            calls["captions"].append(kwargs)
            return _FakeExec(fail=fail_captions)

    class _FakeComments:
        def insert(self, **kwargs):
            calls["comments"].append(kwargs)
            return _FakeExec()

    class _FakeService:
        def videos(self):
            return _FakeVideos()

        def captions(self):
            return _FakeCaptions()

        def commentThreads(self):
            return _FakeComments()

    return _FakeService(), calls


class TestRound17YoutubeUpload(unittest.TestCase):
    def test_build_payload_youtube_shorts_seo(self):
        sb = _sample_sb()
        pl = ytupload.build_payload(sb, title_idx=1, privacy="private")
        sn = pl["body"]["snippet"]
        st = pl["body"]["status"]

        self.assertEqual(sn["title"], "The Weird Reason AI Fails This 2-Second Test")
        self.assertIn("#ai #tech #shorts", sn["description"])
        self.assertEqual(sn["categoryId"], "28")
        self.assertEqual(sn["defaultLanguage"], "en")
        self.assertEqual(sn["defaultAudioLanguage"], "en")
        self.assertIn("ai tokenization", sn["tags"])
        self.assertEqual(st["privacyStatus"], "private")
        self.assertFalse(st["selfDeclaredMadeForKids"])
        self.assertIn("raspberry", pl["pinned_comment"])

        # invalid title_idx raises StudioError
        with self.assertRaises(StudioError):
            ytupload.build_payload(sb, title_idx=9)
        # invalid privacy raises StudioError
        with self.assertRaises(StudioError):
            ytupload.build_payload(sb, privacy="secret")

    def test_trim_tags_respects_limit(self):
        long_tags = [f"very long youtube studio tag number {i}" for i in range(40)]
        kept = ytupload._trim_tags(long_tags, max_total=120)
        self.assertGreater(len(kept), 0)
        self.assertLessEqual(sum(len(t) for t in kept), 120)

    def test_find_video_priority(self):
        sb = _sample_sb("my-slug")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(StudioError):
                ytupload.find_video(tmp, sb)

            out_dir = os.path.join(tmp, "out")
            yt_dir = os.path.join(out_dir, "deliver", "youtube_shorts")
            os.makedirs(yt_dir, exist_ok=True)

            final_p = os.path.join(out_dir, "final.mp4")
            with open(final_p, "wb") as fh:
                fh.write(b"0" * 16)
            self.assertEqual(ytupload.find_video(tmp, sb), final_p)

            vid_p = os.path.join(yt_dir, "video.mp4")
            with open(vid_p, "wb") as fh:
                fh.write(b"1" * 16)
            self.assertEqual(ytupload.find_video(tmp, sb), vid_p)

            slug_p = os.path.join(yt_dir, "my-slug.mp4")
            with open(slug_p, "wb") as fh:
                fh.write(b"2" * 16)
            self.assertEqual(ytupload.find_video(tmp, sb), slug_p)

    def test_upload_dry_run_no_credentials_needed(self):
        sb = _sample_sb("demo-dry")
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "storyboard.json"), "w", encoding="utf-8") as fh:
                json.dump(sb, fh)
            yt_dir = os.path.join(tmp, "out", "deliver", "youtube_shorts")
            os.makedirs(yt_dir, exist_ok=True)
            with open(os.path.join(yt_dir, "demo-dry.mp4"), "wb") as fh:
                fh.write(b"mp4bytes" * 64)
            with open(os.path.join(yt_dir, "captions.srt"), "w", encoding="utf-8") as fh:
                fh.write("1\n00:00:00,000 --> 00:00:01,000\nHello\n")

            logs = []
            res = ytupload.upload(tmp, dry_run=True, log=logs.append)
            self.assertTrue(res["dry_run"])
            self.assertTrue(res["video"].endswith("demo-dry.mp4"))
            self.assertTrue(res["srt"].endswith("captions.srt"))
            self.assertEqual(res["body"]["status"]["privacyStatus"], "private")
            self.assertFalse(os.path.exists(os.path.join(tmp, "out", "youtube_upload.json")))

    def test_upload_full_mocked_with_srt_and_comment(self):
        sb = _sample_sb("demo-live")
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "storyboard.json"), "w", encoding="utf-8") as fh:
                json.dump(sb, fh)
            yt_dir = os.path.join(tmp, "out", "deliver", "youtube_shorts")
            os.makedirs(yt_dir, exist_ok=True)
            with open(os.path.join(yt_dir, "demo-live.mp4"), "wb") as fh:
                fh.write(b"mp4bytes" * 128)
            with open(os.path.join(yt_dir, "captions.srt"), "w", encoding="utf-8") as fh:
                fh.write("1\n00:00:00,000 --> 00:00:01,000\nHello\n")

            fake_yt, calls = _make_fake_youtube(video_id="abc999xyz")
            with mock.patch.object(ytupload, "_media_upload", side_effect=lambda p, *a, **k: {"path": p}):
                res = ytupload.upload(
                    tmp,
                    title_idx=0,
                    privacy="private",
                    upload_srt=True,
                    post_comment=True,
                    service=fake_yt,
                    log=lambda *_: None,
                )

            self.assertEqual(res["video_id"], "abc999xyz")
            self.assertEqual(res["studio_url"], "https://studio.youtube.com/video/abc999xyz/edit")
            self.assertTrue(res["captions_uploaded"])
            self.assertTrue(res["comment_posted"])
            self.assertEqual(res["warnings"], [])
            self.assertEqual(len(calls["videos"]), 1)
            self.assertEqual(len(calls["captions"]), 1)
            self.assertEqual(len(calls["comments"]), 1)
            self.assertEqual(calls["videos"][0]["body"]["status"]["privacyStatus"], "private")

            meta_path = os.path.join(tmp, "out", "youtube_upload.json")
            self.assertTrue(os.path.isfile(meta_path))
            with open(meta_path, encoding="utf-8") as fh:
                saved = json.load(fh)
            self.assertEqual(saved["video_id"], "abc999xyz")

    def test_upload_caption_failure_is_non_fatal(self):
        sb = _sample_sb("demo-warn")
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "storyboard.json"), "w", encoding="utf-8") as fh:
                json.dump(sb, fh)
            out_dir = os.path.join(tmp, "out")
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "final.mp4"), "wb") as fh:
                fh.write(b"mp4bytes" * 64)
            with open(os.path.join(out_dir, "captions.srt"), "w", encoding="utf-8") as fh:
                fh.write("1\n00:00:00,000 --> 00:00:01,000\nHello\n")

            fake_yt, _ = _make_fake_youtube(video_id="warn123", fail_captions=True)
            with mock.patch.object(ytupload, "_media_upload", side_effect=lambda p, *a, **k: {"path": p}):
                res = ytupload.upload(tmp, service=fake_yt, log=lambda *_: None)

            self.assertEqual(res["video_id"], "warn123")
            self.assertFalse(res["captions_uploaded"])
            self.assertEqual(len(res["warnings"]), 1)

    def test_authorize_missing_client_secret_raises_helpful_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_libs = (mock.MagicMock(), mock.MagicMock(), mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
            with mock.patch.object(ytupload, "_load_youtube_libs", return_value=fake_libs):
                with self.assertRaises(StudioError) as ctx:
                    ytupload._authorize(
                        client_secret=os.path.join(tmp, "missing_secret.json"),
                        token_path=os.path.join(tmp, "missing_token.json"),
                    )
            self.assertIn("YOUTUBE_UPLOAD_SETUP.md", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
