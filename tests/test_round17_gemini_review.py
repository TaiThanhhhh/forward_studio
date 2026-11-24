"""Vòng 17 (PR-14) — Gemini Multimodal Video QA (`vidlib/aireview.py`) & Interactions API (`brief.ask`)."""
import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

from vidlib import aireview, brief
from vidlib.common import StudioError


def _make_fake_genai(output_text, state_seq=("PROCESSING", "ACTIVE")):
    calls = {"uploads": [], "creates": [], "deletes": [], "gets": 0}
    states = list(state_seq)

    class _State:
        def __init__(self, name):
            self.name = name

    class _File:
        def __init__(self, name, uri, state):
            self.name = name
            self.uri = uri
            self.mime_type = "video/mp4"
            self.state = _State(state)

    class _Files:
        def upload(self, file):
            calls["uploads"].append(file)
            return _File("files/vid123", "https://generativelanguage.googleapis.com/v1beta/files/vid123", states[0])

        def get(self, name):
            calls["gets"] += 1
            st = states[min(calls["gets"], len(states) - 1)]
            return _File(name, "https://generativelanguage.googleapis.com/v1beta/files/vid123", st)

        def delete(self, name):
            calls["deletes"].append(name)

    class _Interactions:
        def create(self, **kwargs):
            calls["creates"].append(kwargs)
            return types.SimpleNamespace(
                output_text=output_text,
                usage=types.SimpleNamespace(total_input_tokens=120, total_output_tokens=80),
            )

    class _Client:
        def __init__(self, api_key=None):
            self.api_key = api_key
            self.files = _Files()
            self.interactions = _Interactions()

    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    genai_mod.Client = _Client
    google_mod.genai = genai_mod
    return google_mod, genai_mod, calls


class Round17GeminiReviewTests(unittest.TestCase):
    def test_brief_ask_gemini_uses_interactions_api_and_gemini_4_hydrogen(self):
        g_mod, genai_mod, calls = _make_fake_genai('{"topic": "ok"}')
        with (
            mock.patch.dict(sys.modules, {"google": g_mod, "google.genai": genai_mod}),
            mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False),
        ):
            out = brief.ask("gemini", "Write storyboard JSON")
        self.assertEqual(out, '{"topic": "ok"}')
        self.assertEqual(len(calls["creates"]), 1)
        self.assertEqual(calls["creates"][0]["model"], "gemini-4-hydrogen")
        self.assertEqual(brief.LAST_USAGE["model"], "gemini-4-hydrogen")

    def test_review_video_requires_api_key(self):
        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch.object(aireview, "env", return_value=""),
            mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False),
        ):
            with self.assertRaises(StudioError):
                aireview.review_video(d)

    def test_review_video_uploads_polls_writes_reports_and_cleans_up(self):
        payload = {
            "verdict": "READY",
            "clarity_score": 9,
            "muted_hook_score": 9,
            "visual_realism_score": 10,
            "pacing_score": 8,
            "summary": "Hình ảnh chữ bảng phấn khớp 100% lời đọc, tắt tiếng vẫn hiểu ngay.",
            "issues": [
                {"at": "00:18", "severity": "low", "problem": "Chuyển thẻ hơi nhanh", "fix": "Kéo thêm 0.3s giữ chữ"},
            ],
        }
        g_mod, genai_mod, calls = _make_fake_genai(json.dumps(payload))
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "out"), exist_ok=True)
            mp4 = os.path.join(d, "out", "final.mp4")
            with open(mp4, "wb") as fh:
                fh.write(b"\x00" * 2048)
            with (
                mock.patch.dict(sys.modules, {"google": g_mod, "google.genai": genai_mod}),
                mock.patch.object(aireview, "env", return_value="test-key"),
                mock.patch.object(aireview.time, "sleep", return_value=None),
            ):
                res = aireview.review_video(d, log=lambda *_: None)
            self.assertEqual(res["verdict"], "READY")
            self.assertEqual(res["visual_realism_score"], 10)
            self.assertEqual(calls["gets"], 1)
            self.assertEqual(calls["deletes"], ["files/vid123"])
            req = calls["creates"][0]
            self.assertEqual(req["model"], "gemini-4-hydrogen")
            self.assertEqual(req["input"][1]["type"], "video")
            self.assertEqual(req["response_format"]["mime_type"], "application/json")
            self.assertTrue(os.path.exists(os.path.join(d, "qa", "ai_review.json")))
            self.assertTrue(os.path.exists(os.path.join(d, "qa", "ai_review.md")))


if __name__ == "__main__":
    unittest.main()
