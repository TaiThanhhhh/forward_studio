"""Visual regression (AUD-903). Ca thẻ chữ (CPU) luôn chạy; ca engine trình duyệt chạy khi STUDIO_VISUAL=1
(hoặc dùng python scripts/visual_regression.py). Golden ở tests/golden/."""
import os
import unittest

from vidlib import visreg


class SsimMath(unittest.TestCase):
    def test_identical_and_different(self):
        import numpy as np
        a = (np.random.default_rng(1).random((480, 270, 3)) * 255).astype("uint8")
        self.assertAlmostEqual(visreg.ssim(a, a), 1.0, places=6)
        self.assertEqual(visreg.hamming(a, a), 0)
        b = 255 - a
        self.assertLess(visreg.ssim(a, b), 0.5)


class Golden(unittest.TestCase):
    def test_textcard_matches_golden(self):
        rows = visreg.run(cases=["textcard-forward"], log=lambda *_: None)
        self.assertTrue(all(r["ok"] for r in rows), rows)

    @unittest.skipUnless(os.environ.get("STUDIO_VISUAL"), "đặt STUDIO_VISUAL=1 để chạy ca engine trình duyệt")
    def test_engine_frames_match_golden(self):
        rows = visreg.run(log=lambda *_: None)
        self.assertTrue(all(r["ok"] for r in rows), [r for r in rows if not r["ok"]])


if __name__ == "__main__":
    unittest.main()
