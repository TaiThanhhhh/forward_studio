"""Vòng 16 (PR-13) — Lean pipeline, SEO <slug>.mp4 delivery filenames, and cleanup pruning."""
import json
import os
import tempfile
import unittest
from unittest import mock

from vidlib import cleanup, deliver, pipeline


class Round16LeanPipelineTests(unittest.TestCase):
    def test_cleanup_prunes_old_versions_empty_flow_dirs_and_unused_html(self):
        with tempfile.TemporaryDirectory() as d:
            for sub in ("clips", "frames", "refs", "work", "out/versions/v001", "out/versions/v002", "out/deliver/tiktok"):
                os.makedirs(os.path.join(d, sub), exist_ok=True)
            with open(os.path.join(d, "storyboard.json"), "w", encoding="utf-8") as fh:
                json.dump({"shots": [{"id": "C01", "mode_resolved": "code"}]}, fh)
            for rel in ("scripts.html", "prompts.txt", "work/video.mp4",
                        "out/versions/v001/final.mp4", "out/versions/v002/final.mp4", "out/final.mp4"):
                with open(os.path.join(d, rel), "wb") as fh:
                    fh.write(b"x" * 1024)
            ts = cleanup.targets(d, keep_versions=1)
            rels = {os.path.relpath(p, d).replace("\\", "/") for p in ts}
            self.assertIn("out/versions/v001", rels)
            self.assertNotIn("out/versions/v002", rels)
            self.assertIn("scripts.html", rels)
            self.assertIn("prompts.txt", rels)
            self.assertIn("clips", rels)
            self.assertIn("work/video.mp4", rels)
            cleanup.run(d, apply=True, log=lambda *_: None)
            self.assertFalse(os.path.exists(os.path.join(d, "out/versions/v001")))
            self.assertTrue(os.path.exists(os.path.join(d, "out/versions/v002/final.mp4")))
            self.assertTrue(os.path.exists(os.path.join(d, "out/final.mp4")))

    def test_deliver_writes_seo_slug_filename_and_caption_txt(self):
        with tempfile.TemporaryDirectory() as d:
            proj = os.path.join(d, "my-test-video")
            os.makedirs(os.path.join(proj, "out"), exist_ok=True)
            fin = os.path.join(proj, "out", "final.mp4")
            with open(fin, "wb") as fh:
                fh.write(b"0" * 4096)
            sb = {
                "slug": "why-ai-cant-count",
                "title": "Why AI Can't Count",
                "publish": {
                    "youtube_shorts": {
                        "titles": ["Title 1", "Title 2", "Title 3"],
                        "description": "One. Two.",
                        "hashtags": ["ai", "tech", "coding"],
                    },
                    "tiktok": {
                        "caption": "AI sees tokens!",
                        "hashtags": ["ai", "tech", "learnontiktok"],
                    },
                },
            }

            def fake_remux(src, dst, _meta):
                with open(dst, "wb") as fh:
                    fh.write(b"1" * 4096)

            with (
                mock.patch.object(deliver, "_remux", side_effect=fake_remux),
                mock.patch.object(deliver, "cover", return_value=(None, "none")),
                mock.patch.object(deliver, "verify", return_value={"nền tảng test": ("ok", True)}),
            ):
                res = deliver.build(proj, names="youtube_shorts,tiktok", sb=sb, log=lambda *_: None)
            self.assertEqual(res["youtube_shorts"]["video"].replace("\\", "/"),
                             "out/deliver/youtube_shorts/why-ai-cant-count.mp4")
            self.assertEqual(res["tiktok"]["video"].replace("\\", "/"),
                             "out/deliver/tiktok/why-ai-cant-count.mp4")
            self.assertTrue(os.path.exists(os.path.join(proj, "out/deliver/tiktok/caption.txt")))
            self.assertTrue(os.path.exists(os.path.join(proj, "out/deliver/youtube_shorts/caption.txt")))

    def test_s_outro_skips_16x9_endscreen_when_not_requested(self):
        with tempfile.TemporaryDirectory() as d:
            proj = os.path.join(d, "demo-shorts")
            os.makedirs(os.path.join(proj, "out"), exist_ok=True)
            with open(os.path.join(proj, "idea.txt"), "w", encoding="utf-8") as fh:
                fh.write("demo\n")
            r = pipeline.Run(proj, platforms="youtube_shorts,tiktok", log=lambda *_: None)
            r.sb = {"assembly_resolved": "cuts"}
            r.csb = {"outro": {"enabled": True, "mode": "code"}}
            with mock.patch.object(pipeline.outro, "render_endscreen") as rend:
                r.s_outro()
                rend.assert_not_called()


if __name__ == "__main__":
    unittest.main()
