"""Vòng 16 (PR-11) — Board auto-captions burn-in, auto final.mp4 thumbnails, and TikTok bitrate cap."""
import os
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

from engines.board import render as brender
from vidlib import autocaptions, boardplan, encode, thumbs


class Round16BoardPolishTests(unittest.TestCase):
    def test_board_defaults_use_crf_19_and_10m_maxrate(self):
        cfg = boardplan.cfg()
        self.assertEqual(cfg.get("crf"), 19)
        self.assertEqual(cfg.get("maxrate"), "10M")
        args = encode.video_args("master", 30, crf=19, maxrate="10M")
        self.assertIn("-crf", args)
        self.assertEqual(args[args.index("-crf") + 1], "19")
        self.assertIn("-maxrate", args)
        self.assertEqual(args[args.index("-maxrate") + 1], "10M")
        self.assertEqual(args[args.index("-bufsize") + 1], "20M")

    def test_apply_caption_bgr_draws_onto_board_frame(self):
        vo = {
            "lines": [
                {
                    "text": "One line burned everything",
                    "words": [
                        {"w": "One", "start": 0.1, "end": 0.4},
                        {"w": "line", "start": 0.4, "end": 0.8},
                        {"w": "burned", "start": 0.8, "end": 1.2},
                    ],
                }
            ]
        }
        layer = autocaptions.Layer(vo, "studio_clean", "board-black")
        dark = np.zeros((1920, 1080, 3), dtype=np.uint8)
        out = brender._apply_caption_bgr(dark, layer, 0.55)
        self.assertEqual(out.shape, dark.shape)
        self.assertGreater(int(out.sum()), 0, "studio_clean caption should paint visible pixels in Zone C")
        silent = brender._apply_caption_bgr(dark, layer, 5.0)
        self.assertEqual(int(silent.sum()), 0)

    def test_thumbs_background_falls_back_to_final_mp4_before_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "out"), exist_ok=True)
            mp4 = os.path.join(d, "out", "final.mp4")
            with open(mp4, "wb") as fh:
                fh.write(b"\x00" * 4096)
            fake_img = Image.new("RGB", (1080, 1920), (18, 22, 26))
            sb = {
                "shots": [
                    {"id": "C01", "beat": "hook", "start_frame": {"file": "frames/C01.png"}, "board": {"lines": ["A"]}},
                ]
            }
            v = {"id": "T1", "archetype": "before_disaster", "file": "thumbnails/bg_T1.png"}
            with (
                mock.patch("vidlib.common.probe", return_value={"duration": 30.0}),
                mock.patch.object(thumbs, "_frame_at", return_value=fake_img),
            ):
                im, src = thumbs.background(d, sb, v, (1080, 1920), {}, lambda _: None)
            self.assertEqual(im.size, (1080, 1920))
            self.assertTrue(src.startswith("final "), f"expected final.mp4 frame source, got {src}")


if __name__ == "__main__":
    unittest.main()
