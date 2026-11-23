"""Kiểm nâng cấp vòng 11: CapCut auto-captions, style Vox & Cartoon Story, set 3D stadium/diorama, transition dip."""
import unittest

import numpy as np
from PIL import Image

from engines import adapter, html
from vidlib import autocaptions, codeshot, fx, spine, styles


def _sample_vo():
    return {
        "lines": [
            {
                "words": [
                    {"w": "A", "start": 0.0, "end": 0.15},
                    {"w": "horse", "start": 0.16, "end": 0.45},
                    {"w": "sprints", "start": 0.46, "end": 0.85},
                    {"w": "twice", "start": 0.86, "end": 1.15},
                    {"w": "as", "start": 1.16, "end": 1.3},
                    {"w": "fast,", "start": 1.31, "end": 1.65},
                ]
            }
        ]
    }


class Round11Tests(unittest.TestCase):
    def test_autocaptions_chunks_and_all_presets(self):
        vo = _sample_vo()
        chunks = autocaptions.build_chunks(vo, max_words=3, max_chars=22)
        self.assertEqual(len(chunks), 2)
        self.assertEqual([w["w"] for w in chunks[0]["words"]], ["A", "horse", "sprints"])
        base = Image.new("RGB", (1080, 1920), (10, 12, 16))
        for preset in ("capcut_pop", "capcut_pill", "capcut_box", "vox_highlight"):
            layer = autocaptions.Layer(vo, preset=preset, style="flat-vector-black")
            out = layer.draw(base.copy(), 0.25)
            self.assertEqual(out.size, (1080, 1920))
            self.assertGreater(int(np.abs(np.asarray(out, np.int16) - np.asarray(base, np.int16)).sum()), 1000)
        off = autocaptions.Layer(vo, preset="off")
        self.assertTrue(np.array_equal(np.asarray(off.draw(base.copy(), 0.25)), np.asarray(base)))

    def test_autocaptions_resolve_priority(self):
        self.assertEqual(autocaptions.resolve_preset({"captions": "capcut_pill"}, None, "vox-editorial-black"),
                         "capcut_pill")
        self.assertEqual(autocaptions.resolve_preset({"captions": "capcut_pill"}, "capcut_box", "vox-editorial-black"),
                         "capcut_box")
        self.assertEqual(autocaptions.resolve_preset({}, None, "vox-editorial-black"), "vox_highlight")
        self.assertEqual(autocaptions.resolve_preset({}, None, "cartoon-story-black"), "capcut_box")
        self.assertEqual(autocaptions.resolve_preset({"captions": False}, None, "vox-editorial-black"), "off")

    def test_vox_and_cartoon_story_styles_registered(self):
        avail = styles.available()
        self.assertIn("vox-editorial-black", avail)
        self.assertIn("cartoon-story-black", avail)
        self.assertIn("vox", html.LOOKS)
        self.assertIn("story", html.LOOKS)
        self.assertIn("vox", spine.LOOK_MOVES)
        self.assertIn("story", spine.LOOK_MOVES)
        for st in ("vox-editorial-black", "cartoon-story-black"):
            w, cp = codeshot.world(st)
            self.assertTrue(w.get("colors") and cp)

    def test_stadium_and_diorama_sets_and_dip_transition(self):
        voc = adapter.creature_vocab()
        self.assertIn("stadium", voc["sets"])
        self.assertIn("diorama", voc["sets"])
        self.assertEqual(adapter.validate_three("stage", {"set": "stadium", "props": [{"id": "r", "type": "adult"}]}), [])
        self.assertEqual(adapter.validate_three("stage", {"set": "diorama", "props": [{"id": "h", "type": "horse"}]}), [])
        a = Image.new("RGB", (1080, 1920), (200, 50, 50))
        b = Image.new("RGB", (1080, 1920), (50, 200, 50))
        mid = fx.transition(b, a, "dip", 1)
        self.assertEqual(mid.size, (1080, 1920))
        self.assertLess(float(np.asarray(mid).mean()), 120.0)


if __name__ == "__main__":
    unittest.main()
