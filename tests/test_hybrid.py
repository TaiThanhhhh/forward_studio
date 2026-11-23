"""Vòng 8: trộn nhiều engine trong một video (3D three.js + chart html + manim) và các look 3D của engine three.js."""
import os
import re
import unittest

from engines import adapter
from vidlib import brief, codeshot, styles, textstyle
from vidlib.common import ROOT


def look3d_kinds():
    """Tên preset trong `const LOOK3D = {…}` của engines/three/main.js (một nguồn sự thật)."""
    with open(os.path.join(ROOT, "engines", "three", "main.js"), encoding="utf-8") as fh:
        body = fh.read().split("const LOOK3D = {", 1)[1].split("\n};", 1)[0]
    return set(re.findall(r"^\s{2}(\w+):", body, re.M))


class TestRouting(unittest.TestCase):
    def test_same_name_scene_routes_by_params(self):
        # `scale` có ở cả three.js (cân đĩa) và html (thang kích thước): style 3D + params html → html
        html_scale = {"code": {"scene": "scale", "params": {"items": [{"label": "ATP", "size": 4}]}}}
        three_scale = {"code": {"scene": "scale", "params": {"ball_g": 100, "cubes": 3}}}
        self.assertEqual(codeshot.engine_of(html_scale, "toon3d-lab"), "html")
        self.assertEqual(codeshot.engine_of(three_scale, "toon3d-lab"), "three")
        self.assertEqual(codeshot.engine_of({"code": {"scene": "outro", "params": {"teaser": "x"}}}, "toon3d-lab"), "three")
        self.assertEqual(codeshot.engine_of({"code": {"scene": "graph", "params": {"points": [[0, 0]]}}}, "toon3d-lab"),
                         "html")
        self.assertEqual(codeshot.engine_of({"code": {"engine": "manim", "scene": "graph"}}, "toon3d-lab"), "manim")

    def test_three_param_names_read_from_scene_header(self):
        self.assertIn("ball_g", adapter.three_param_names("scale"))
        self.assertIn("teaser", adapter.three_param_names("outro"))
        self.assertNotIn("0", adapter.three_param_names("scale"))
        self.assertEqual(adapter.three_param_names("no-such-scene"), set())

    def test_mix_help_lists_only_real_scenes(self):
        txt = brief.mix_help()
        three = set(codeshot.scenes("three"))
        for name in re.findall(r"`(\w+)`", txt.split("engine `three`:", 1)[1].split("\n", 1)[0]):
            if name != "stage":
                self.assertIn(name, three)
        self.assertNotIn("`gauge`", txt.split("engine `three`:", 1)[1].split("\n", 1)[0])


class TestManimPalette(unittest.TestCase):
    def test_dark_colours_lifted_for_thin_lines(self):
        from engines.manim import _lift
        self.assertEqual(_lift("#FFD27A"), "#FFD27A")          # đủ sáng → giữ nguyên
        lifted = _lift("#1849F7")
        self.assertNotEqual(lifted, "#1849F7")
        self.assertGreater(int(lifted[1:3], 16), 0x18)


class TestLook3D(unittest.TestCase):
    def test_every_look3d_style_uses_a_known_preset(self):
        kinds = look3d_kinds()
        self.assertTrue({"toon", "clay", "plastic", "glass", "chrome", "lowpoly", "paper", "holo", "xray"} <= kinds)
        found = 0
        for sid in textstyle.list_styles():
            lk = (textstyle.load_style(sid).get("world") or {}).get("look3d")
            if not lk:
                continue
            found += 1
            kind = lk if isinstance(lk, str) else lk.get("kind", "toon")
            self.assertIn(kind, kinds, sid)
        self.assertGreaterEqual(found, 8)

    def test_3d_styles_registered_and_routed(self):
        for sid in ("xray3d-black", "glass3d-black", "chrome3d-black", "lowpoly3d-black", "hologram3d-black",
                    "plastic-toy3d-black", "papercraft3d-black", "clay3d-black"):
            self.assertIn(sid, styles.PREFERENCE)
            st = textstyle.load_style(sid)
            self.assertTrue((st.get("flow") or {}).get("is_3d"), sid)
            self.assertIn("html", st, sid)                       # chart/số liệu trong video 3D dùng palette của style
            if st.get("code_only"):
                self.assertEqual(styles.engine(sid), "three", sid)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "styles", f"{sid}.md")), sid)

    def test_three_job_carries_look3d(self):
        w, _ = codeshot.world("xray3d-black")
        self.assertEqual(w.get("look3d"), "xray")
        w, _ = codeshot.world("toon3d-lab")
        self.assertIsNone(w.get("look3d"))


if __name__ == "__main__":
    unittest.main()
