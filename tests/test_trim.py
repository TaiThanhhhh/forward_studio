"""Auto-trim bằng clip giả: đầu tĩnh, đuôi giảm tốc, scene cut, bỏ audio khi ingest."""
import os
import tempfile
import unittest

import numpy as np

from vidlib import fakes, ingest, motion
from vidlib.common import probe


class TrimNumpy(unittest.TestCase):
    CASES = [dict(), dict(head_sec=0.8, decel_sec=1.4), dict(duration=4.0, head_sec=0.4, decel_sec=0.8, hold_sec=0.2),
             dict(duration=6.0, head_sec=1.0, decel_sec=1.5, hold_sec=0.5)]

    def test_head_and_tail(self):
        for kw in self.CASES:
            fr, gt = fakes.frames_like(**kw)
            a = motion.analyze(frames=fr)
            decel = gt["stop"] - gt["decel_start"]
            self.assertLessEqual(abs(a["head_end"] - gt["head_end"]), 2, kw)
            # đuôi: cắt trước khi tốc độ rơi quá 50% (≤ 35% vùng giảm tốc), không cắt vào phần chạy đều
            self.assertGreaterEqual(a["tail_start"], gt["decel_start"] - 2, kw)
            self.assertLessEqual(a["tail_start"], gt["decel_start"] + int(0.35 * decel), kw)

    def test_window_inside_clean_zone(self):
        fr, gt = fakes.frames_like()
        a = motion.analyze(frames=fr)
        lo, hi, how = motion.choose_window(a, 54)
        self.assertEqual(how, "best")
        self.assertGreaterEqual(lo, a["head_end"])
        self.assertLessEqual(hi, a["tail_start"])
        lo, hi, how = motion.choose_window(a, 40, anchor="end")
        self.assertEqual(hi, a["tail_start"])
        lo, hi, how = motion.choose_window(a, 40, anchor="start")
        self.assertEqual(lo, a["head_end"])

    def test_scene_cut_never_crossed(self):
        fr, gt = fakes.frames_like(cut_at=2.0)
        a = motion.analyze(frames=fr)
        self.assertIn(gt["cut"], a["cuts"])
        for need in (30, 54, 80):
            lo, hi, _ = motion.choose_window(a, need)
            self.assertFalse(lo < gt["cut"] < hi, (need, lo, hi))

    def test_static_clip(self):
        fr = np.random.default_rng(0).normal(0, 0.6, (90, 192, 108)).astype(np.float32)
        a = motion.analyze(frames=fr)
        self.assertFalse(a["active"])
        self.assertEqual((a["head_end"], a["tail_start"]), (0, 90))


class TrimFfmpeg(unittest.TestCase):
    """Clip giả thật (H.264 + audio rác) → ingest → phân tích."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.src = os.path.join(cls.tmp.name, "Flow_video_001.mp4")
        cls.gt = fakes.make_clip(cls.src, duration=4.0, size=(360, 640), head_sec=0.6, decel_sec=1.0, hold_sec=0.3)
        cls.dst = os.path.join(cls.tmp.name, "ing", "C01.mp4")
        cls.info = ingest.normalize_clip(cls.src, cls.dst)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_ingest_drops_audio_and_normalizes(self):
        self.assertEqual(probe(self.src)["audio_streams"], 1)
        out = probe(self.dst)
        self.assertEqual(out["audio_streams"], 0)
        self.assertEqual((out["width"], out["height"]), (1080, 1920))
        self.assertAlmostEqual(out["fps"], 30.0, places=2)
        self.assertEqual(self.info["src_audio_streams"], 1)

    def test_trim_on_real_file(self):
        a = motion.analyze(self.dst)
        self.assertLessEqual(abs(a["head_end"] - self.gt["head_end"]), 2)
        decel = self.gt["stop"] - self.gt["decel_start"]
        self.assertGreaterEqual(a["tail_start"], self.gt["decel_start"] - 2)
        self.assertLessEqual(a["tail_start"], self.gt["decel_start"] + int(0.35 * decel))

    def test_seed_frame_export(self):
        png = os.path.join(self.tmp.name, "frames", "C02_start.png")
        motion.export_frame(self.dst, 2.0, png)
        self.assertTrue(os.path.getsize(png) > 1000)


if __name__ == "__main__":
    unittest.main()
