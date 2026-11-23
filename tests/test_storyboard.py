import json
import os
import unittest

from tests.helpers import demo_raw
from vidlib import storyboard
from vidlib.common import PROMPTS_DIR


class Schema(unittest.TestCase):
    def test_demo_valid(self):
        sb = storyboard.normalize(demo_raw())
        self.assertEqual(storyboard.validate(sb), ([], []))

    def test_schema_example_in_brief_is_valid(self):
        with open(os.path.join(PROMPTS_DIR, "storyboard_schema.json"), encoding="utf-8") as f:
            raw = json.load(f)
        raw["flow"] = {}
        sb = storyboard.normalize(raw)
        errs, _ = storyboard.validate(sb)
        self.assertEqual(errs, [])

    def test_defaults(self):
        sb = storyboard.normalize({"topic": "t", "shots": [{"id": "C1", "start_frame": "a ball", "action": "it rolls"}]})
        s = sb["shots"][0]
        self.assertEqual(s["id"], "C01")
        self.assertEqual(s["mode"], "auto")
        self.assertEqual(s["start_frame"]["desc"], "a ball")
        self.assertEqual(s["start_frame"]["file"], "frames/C01_start.png")
        self.assertEqual(s["clip_file"], "clips/C01.mp4")
        self.assertEqual(s["trim"], {"in": None, "out": None, "speed": 1.0})
        self.assertEqual(s["action"], [{"t": None, "do": "it rolls"}])
        self.assertTrue(sb["flow"]["video_model"])

    def test_errors(self):
        sb = storyboard.normalize({"topic": "t", "shots": [
            {"id": "C01", "mode": "text_to_video", "refs": ["REF_X"], "start_frame": "a", "action": "b",
             "continues_from": "C02"},
            {"id": "C02", "beat": "climax", "transition_in": "dissolve", "start_frame": "a", "action": "b",
             "onscreen": [{"kind": "banner", "text": "x"}]},
        ]})
        errs, _ = storyboard.validate(sb)
        joined = " | ".join(errs)
        for needle in ("mode 'text_to_video'", "REF_X", "ĐỨNG TRƯỚC", "beat 'climax'", "'dissolve'", "'banner'"):
            self.assertIn(needle, joined)

    def test_unknown_model(self):
        sb = storyboard.normalize({"topic": "t", "shots": [{"start_frame": "a", "action": "b"}]}, "Sora 9")
        self.assertTrue(any("Sora 9" in e for e in storyboard.validate(sb)[0]))

    def test_model_override(self):
        sb = storyboard.normalize(demo_raw(), "Veo 3.1 Lite")
        self.assertEqual(sb["flow"]["video_model"], "Veo 3.1 Lite")


if __name__ == "__main__":
    unittest.main()
