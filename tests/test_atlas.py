"""3D Style Atlas → preset dark-stage (vòng 8): đủ 37 style, khung chuẩn, không chép nguyên văn, bộ chọn tự động
bỏ off-brand/tier 2, compiler dùng block ngắn mà vẫn giữ AUDIO im lặng + AVOID + chỗ chừa chữ."""
import os
import unittest
from unittest import mock

from vidlib import atlas, compiler, linter, storyboard, styles, textstyle
from vidlib.common import ROOT


class AtlasConfig(unittest.TestCase):
    def test_37_styles_in_7_categories(self):
        es = atlas.entries()
        self.assertEqual(sorted(e["n"] for e in es), list(range(1, 38)))
        cats = atlas.config()["categories"]
        self.assertEqual(len(cats), 7)
        for c in cats:
            self.assertEqual(sum(1 for e in es if e["cat"] == c["id"]), c["count"], c["id"])

    def test_tier1_size_and_spread(self):
        t1 = [e for e in atlas.entries() if e["tier"] == 1]
        self.assertTrue(10 <= len(t1) <= 15, len(t1))
        self.assertGreaterEqual(len({e["cat"] for e in t1}), 6)
        self.assertFalse([e["id"] for e in t1 if e["brand_fit"] == "off-brand"])
        self.assertFalse([e["id"] for e in t1 if e["fit"] < 4])


class AtlasPresets(unittest.TestCase):
    def setUp(self):
        textstyle.load_style.cache_clear()

    def test_presets_written_and_valid(self):
        for e in atlas.entries():
            sid = atlas.style_id(e)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "styles", f"{sid}.json")), sid)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "styles", f"{sid}.md")), sid)
            st = textstyle.load_style(sid)
            self.assertEqual(atlas.check(e, st), [], sid)
            self.assertEqual(st["variant"], "dark-stage")
            self.assertEqual(st["palette"]["bg"], "#000000")
            self.assertIn(st["brand_fit"], atlas.BRAND_FIT)
            if e["engine"] in ("three", "hybrid"):
                self.assertTrue(st["world"].get("look3d"), sid)
            self.assertEqual(st["code_only"], e["engine"] == "three")

    def test_preset_file_matches_generator(self):
        """styles/atlas-*.json là bản sinh — sửa config/atlas.json rồi chạy scripts/atlas_import.py (không sửa tay)."""
        import json
        for e in atlas.entries()[:5]:
            with open(os.path.join(ROOT, "styles", f"{atlas.style_id(e)}.json"), encoding="utf-8") as fh:
                on_disk = json.load(fh)
            self.assertEqual(on_disk, json.loads(json.dumps(atlas.preset(e))), atlas.style_id(e))

    def test_hot_color_is_warm(self):
        """Bi thép nóng (danger) + vai 'hot' của chart = màu ấm nhất của style; không có màu ấm → defaults.hot_fallback.
        Nước đá luôn lạnh (base chrome để nước màu cam → đổi sang màu lạnh của bảng màu)."""
        self.assertEqual(atlas.warm_key({"a": "#3F6BFF", "b": "#FF5A3C", "c": "#22C36E"}), "b")
        self.assertIsNone(atlas.warm_key({"a": "#0b6a7c", "b": "#9a9a9a", "c": "#ffffff"}))
        for e in atlas.entries():
            st = atlas.preset(e)
            k = atlas.warm_key(e["palette"])
            if k:
                self.assertEqual(st["world"]["colors"]["danger"], e["palette"][k], e["id"])
                self.assertEqual(st["html"]["roles"]["hot"], k, e["id"])
            else:                   # không có màu ấm (vd Studio Product) → vẫn nóng, không lấy màu lạnh của base chrome
                self.assertEqual(st["html"]["palette"][st["html"]["roles"]["hot"]], "#FF5A3C", e["id"])
            if "world" in st:
                self.assertIsNotNone(atlas.warm_key({"x": st["world"]["colors"]["danger"]}, ("x",)), e["id"])
                self.assertIsNone(atlas.warm_key({"x": st["world"]["colors"]["water"]}, ("x",)), e["id"])  # nước đá không ấm

    def test_copy_guard(self):
        theirs = "A pop-up book open on a wooden table in lamplight with layered card scenes"
        self.assertTrue(atlas.copied_phrases("we see a pop-up book open on a wooden table today", theirs))
        self.assertFalse(atlas.copied_phrases("a folding paper book under a warm lamp", theirs))


class AtlasAutoPick(unittest.TestCase):
    def setUp(self):
        textstyle.load_style.cache_clear()

    def test_auto_ok(self):
        self.assertTrue(styles.auto_ok("atlas-neon-sign"))          # tier 1, ok
        self.assertFalse(styles.auto_ok("atlas-painted"))           # off-brand
        self.assertFalse(styles.auto_ok("atlas-low-poly"))          # tier 2
        self.assertTrue(styles.auto_ok("forward"))                  # style cũ không bị ảnh hưởng

    def test_off_brand_never_ranked_even_on_topic(self):
        with mock.patch.object(styles, "history", return_value=[]):
            names = [s for s, _ in styles.ranked({"topic": "a painting of a farm village with bread in the countryside"})]
        self.assertNotIn("atlas-painted", names)
        self.assertFalse([n for n in names if n.startswith("atlas-") and not styles.auto_ok(n)])

    def test_manual_pick_still_allowed(self):
        self.assertEqual(styles.plan("anything", style="atlas-painted")["style"], "atlas-painted")

    def test_recent_atlas_style_avoided(self):
        hist = [(3.0, "v3", "atlas-glass-and-light"), (2.0, "v2", "forward"), (1.0, "v1", "chalk")]
        with mock.patch.object(styles, "history", return_value=hist):
            names = [s for s, _ in styles.ranked({"topic": "What happens if you mix acid and oil in a glass?"})]
        self.assertNotIn("atlas-glass-and-light", names)


class AtlasCompiler(unittest.TestCase):
    def setUp(self):
        textstyle.load_style.cache_clear()

    def _sb(self, style):
        sb = storyboard.normalize({"topic": "What happens if you drop a hot steel ball into ice water?",
                                   "style": style,
                                   "shots": [{"id": "C01", "subject": "a glowing steel ball above a glass of ice water",
                                              "start_frame": {"desc": "a glowing steel ball hangs above ice water"},
                                              "end_frame": {"desc": "steam bursts from the glass"},
                                              "action": "the ball drops into the water and steam bursts out"}]})
        sb["style_resolved"] = style
        return compiler.compile_all(sb)

    def test_hybrid_preset_prompts(self):
        c = self._sb("atlas-glass-and-light")
        s = c["shots"][0]
        self.assertNotEqual(s["mode_resolved"], "code")
        fp, vp = s["start_frame"]["prompt"], s["video_prompt"]
        self.assertIn("3D lab glassware still life", fp)
        self.assertIn("empty (captions are added later)", fp)
        self.assertIn("red", fp)                                   # accent của style, không phải accent brand
        self.assertNotIn("3D render", fp)
        self.assertIn("Audio: complete silence", vp)
        self.assertIn("Avoid:", vp)
        self.assertIn("Motion starts on the very first frame", vp)
        mo = next(e for e in atlas.entries() if e["id"] == "glass-and-light")["motion"]
        self.assertIn(mo.lower()[:30], vp.lower())                  # chuyển động của chính style này
        self.assertLessEqual(compiler.word_count(vp), 170)
        self.assertFalse([i for i in linter.lint(c) if i.get("level") == "error" and "C01" in str(i)], linter.lint(c))

    def test_avoid_add_from_style(self):
        c = self._sb("atlas-neon-sign")
        self.assertIn("readable signage", c["shots"][0]["video_prompt"])

    def test_old_styles_unchanged(self):
        c = self._sb("forward")
        vp = c["shots"][0]["video_prompt"]
        self.assertIn(compiler.block("motion"), vp)
        self.assertNotIn("captions are added later", c["shots"][0]["start_frame"]["prompt"])


if __name__ == "__main__":
    unittest.main()
