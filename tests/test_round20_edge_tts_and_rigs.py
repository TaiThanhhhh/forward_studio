"""Vòng 20 (PR-18): kiểm tra nhân vật 2D mới (`duck`, `owl`, `scientist`) và fallback giọng miễn phí Edge Neural TTS."""
import unittest

from engines.html import rig2d
from vidlib import tts


class TestRound20EdgeTtsAndRigs(unittest.TestCase):
    def test_new_explainer_rigs_in_vocab(self):
        sp = set(rig2d.species())
        for name in ("duck", "owl", "scientist"):
            self.assertIn(name, sp)
            self.assertIsNone(rig2d.check(f"rig:{name}:idle:happy"))
        # vòng 21: bí danh mang tên kênh khác bị bỏ (brand-safety)
        self.assertIsNotNone(rig2d.check("rig:kurzbird:wave:happy"))
        self.assertIsNone(rig2d.check("rig:doctor:point:neutral"))
        self.assertIsNone(rig2d.check("rig:kitty:sit:love"))

    def test_edge_voice_mapping_and_boundary_alignment(self):
        self.assertEqual(tts._edge_voice_for("George"), "en-GB-RyanNeural")
        self.assertEqual(tts._edge_voice_for("Sarah"), "en-US-AvaMultilingualNeural")
        self.assertEqual(tts._edge_voice_for("edge:en-US-GuyNeural"), "en-US-GuyNeural")

        lines = [
            {"text": "Twenty-four hours later, your brain resets.", "beat": "hook"},
        ]
        cfg = {**tts.voice_cfg(), "audio_tags": {"enabled": False}}
        spoken, words = tts.build_text(lines, cfg)
        bounds = [
            ("Twenty", 0.05, 0.30),
            ("four", 0.31, 0.55),
            ("hours", 0.56, 0.85),
            ("later", 0.86, 1.15),
            ("your", 1.16, 1.32),
            ("brain", 1.33, 1.65),
            ("resets", 1.66, 2.10),
        ]
        wt = tts._align_boundary_words(spoken, words, bounds)
        self.assertEqual(len(wt), len(words))
        self.assertEqual(wt[0]["w"], "Twenty-four")
        self.assertEqual(wt[0]["start"], 0.05)
        self.assertEqual(wt[0]["end"], 0.55)
        self.assertEqual(wt[-1]["w"], "resets.")
        self.assertEqual(wt[-1]["end"], 2.10)


if __name__ == "__main__":
    unittest.main()
