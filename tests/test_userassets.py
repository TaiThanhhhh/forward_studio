"""Vòng 10b: tài sản người dùng + thư viện mới — SVG (SVGO → parts), Lottie (dotLottie), Rive, hậu kỳ postprocessing.
Ca chạy trình duyệt (Edge headless) cần STUDIO_VISUAL=1 như tests/test_visual.py; phần còn lại chạy bằng Python/Node."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from engines import adapter, html
from vidlib import codeshot, userassets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEAR = "tests/fixtures/svg/gear-badge.json"
LOTTIE = "tests/fixtures/lottie/pulse.json"
RIVE = "tests/fixtures/rive/truck.riv"
VISUAL = unittest.skipUnless(os.environ.get("STUDIO_VISUAL"), "đặt STUDIO_VISUAL=1 để chạy ca engine trình duyệt")


def node(code):
    r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout.strip())


class Resolve(unittest.TestCase):
    def test_svg_lottie_rive_names_resolve_per_engine(self):
        p = {"actors": [{"id": "a", "icon": "svg:" + GEAR}, {"id": "l", "lottie": LOTTIE}, {"id": "r", "rive": RIVE}],
             "left": {"icon": "svg:" + GEAR}}
        out = userassets.resolve(p, "html")
        self.assertIsInstance(out["actors"][0]["icon"], dict)
        self.assertGreater(len(out["actors"][0]["icon"]["parts"]), 2)
        self.assertEqual(out["left"]["icon"], out["actors"][0]["icon"])
        self.assertEqual(out["actors"][1]["lottie_url"], "/" + LOTTIE)
        self.assertEqual(out["actors"][2]["rive_url"], "/" + RIVE)
        self.assertEqual(p["actors"][0]["icon"], "svg:" + GEAR)                  # params gốc không bị sửa
        t = userassets.resolve({"props": [{"id": "g", "type": "svg:" + GEAR}]}, "three")
        self.assertEqual(t["props"][0]["type"], "svgicon")
        self.assertTrue(t["props"][0]["icon_parts"])

    def test_missing_assets_and_license_notes(self):
        errs = userassets.errors({"actors": [{"icon": "svg:nope"}, {"lottie": "nope"}, {"rive": "nope"}]})
        self.assertEqual(len(errs), 3)
        self.assertIn("studio.py svg", errs[0])
        self.assertEqual(html.validate("scene", {"actors": [{"id": "a", "icon": "svg:" + GEAR}]}), [])
        self.assertTrue(html.validate("scene", {"actors": [{"id": "a", "icon": "svg:nope"}]}))
        self.assertTrue(adapter.validate_three("stage", {"props": [{"type": "svg:nope"}]}))
        notes = userassets.license_notes({"actors": [{"icon": "svg:" + GEAR}, {"lottie": LOTTIE}]})
        self.assertEqual([n[0] for n in notes], ["svg", "lottie"])
        self.assertTrue(notes[0][2])                                              # SVG mẫu có ghi giấy phép
        self.assertIsNone(notes[1][2])                                            # Lottie mẫu chưa có .license.txt

    def test_brief_lists_user_assets(self):
        from vidlib import brief
        self.assertIn("svg:<name>", brief._user_assets_help())


@unittest.skipUnless(shutil.which("node"), "cần node")
class NodeSide(unittest.TestCase):
    def test_lottie_recolor_modes(self):
        out = node("""
        import { recolorLottie } from './engines/html/media.js';
        import fs from 'fs';
        const src = JSON.parse(fs.readFileSync('LOTTIE_PATH', 'utf8'));
        const col = (r) => ({ hot: '#ff0000', cold: '#0000ff', accent: '#00ff00', ink: '#ffffff', dim: '#777777' })[r] || r;
        const pick = (j) => j.layers[0].shapes[0].it.filter((x) => x.ty === 'fl' || x.ty === 'st')
          .map((x) => x.c.k.slice(0, 3));
        console.log(JSON.stringify({
          keep: pick(recolorLottie(structuredClone(src), 'keep', col, '#000000')),
          pal: pick(recolorLottie(structuredClone(src), 'palette', col, '#000000')),
          tint: pick(recolorLottie(structuredClone(src), 'accent', col, '#000000')) }));
        """.replace("LOTTIE_PATH", LOTTIE))
        self.assertEqual(out["keep"], [[0.95, 0.35, 0.2], [0.1, 0.45, 0.95]])
        self.assertEqual(out["pal"], [[1, 0, 0], [0, 0, 1]])                     # cam → vai hot, xanh → vai cold
        self.assertTrue(all(c[0] == 0 and c[2] == 0 and 0 < c[1] <= 1 for c in out["tint"]))

    def test_parts_holes_expand(self):
        out = node("""
        import { partsIcon } from './engines/html/icons.js';
        const p = partsIcon({ parts: [{ k: 'poly', pts: [[-1,-1],[1,-1],[1,1],[-1,1]], role: 'hot',
                                         holes: [[[-0.3,-0.3],[0.3,-0.3],[0.3,0.3],[-0.3,0.3]]] }] });
        console.log(JSON.stringify(p.map((x) => [x.k, x.role, !!x.hole, 'holes' in x])));
        """)
        self.assertEqual(out, [["poly", "hot", False, False], ["poly", "hot", True, False]])


@VISUAL
class Browser(unittest.TestCase):
    def test_svg_import_roles_holes_and_strokes(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "svg", "gear-badge.svg"), encoding="utf-8") as fh:
            res = userassets.svg_to_parts(fh.read())
        parts = res["parts"]
        self.assertEqual(sorted(p["role"] for p in parts), ["accent", "cold", "hot", "ink"])
        ring = next(p for p in parts if p["role"] == "hot")
        self.assertEqual(len(ring.get("holes", [])), 1)                          # vòng có lỗ
        self.assertTrue(any(p["k"] == "line" for p in parts))                     # polyline chỉ có viền → line
        allpts = [q for p in parts for q in p["pts"]]
        self.assertAlmostEqual(max(max(abs(x), abs(y)) for x, y in allpts), 1.0, delta=0.02)   # chuẩn hoá -1..1

    def _render(self, eng, scene, params, style, frames, sub, only=None):
        work = tempfile.mkdtemp(prefix="ua-", dir=os.path.join(ROOT, "qa"))
        self.addCleanup(shutil.rmtree, work, True)
        spec = adapter.ShotSpec(sid="T", engine=eng, scene=scene, params=params, frames=frames, fps=30, style=style,
                                work=work)
        job = adapter.get(eng).job(spec)
        d = os.path.join(work, sub)
        adapter.get(eng).render(job, d, only, log=lambda *a: None)
        return d, job

    def test_lottie_and_rive_render_same_frame_in_any_order(self):
        """Worker nào render frame nào cũng ra cùng hình (Rive được tua, Lottie setFrame đồng bộ)."""
        import numpy as np
        from PIL import Image
        params = {"actors": [{"id": "l", "lottie": LOTTIE, "x": 0.35, "y": 0.35, "size": 420},
                             {"id": "r", "rive": RIVE, "x": 0.5, "y": 0.65, "size": 640}]}
        full, job = self._render("html", "scene", params, "flat-vector-black", 16, "all")
        meta = adapter.get("html").meta(job)
        self.assertEqual({m["kind"] for m in meta["media"]}, {"lottie", "rive"})
        one = os.path.join(os.path.dirname(full), "one")
        adapter.get("html").render(job, one, [11], log=lambda *a: None)
        a = np.asarray(Image.open(os.path.join(full, "f0011.jpg"))).astype(int)
        b = np.asarray(Image.open(os.path.join(one, "f0011.jpg"))).astype(int)
        self.assertLess(np.abs(a - b).max(), 3)
        f2 = np.asarray(Image.open(os.path.join(full, "f0002.jpg"))).astype(int)
        self.assertGreater(np.abs(a - f2).mean(), 0.5)                            # có chuyển động

    def test_postprocessing_opt_in_keeps_black_and_is_deterministic(self):
        import numpy as np
        from PIL import Image
        orig = codeshot.world

        def world(style):
            w, cp = orig(style)
            return {**w, "look3d": {"kind": "toon", "post": {"smaa": True, "ca": 0.002, "bloom": {}}}}, cp

        codeshot.world = world
        self.addCleanup(setattr, codeshot, "world", orig)
        params = {"props": [{"id": "b", "type": "ball", "at": [0, 0.3, 0]},
                            {"id": "s", "type": "svg:" + GEAR, "at": [0.5, 0, 0]}]}
        full, job = self._render("three", "stage", params, "toon3d-lab", 6, "all")
        one = os.path.join(os.path.dirname(full), "one")
        adapter.get("three").render(job, one, [4], log=lambda *a: None)
        a = np.asarray(Image.open(os.path.join(full, "f0004.jpg"))).astype(int)
        b = np.asarray(Image.open(os.path.join(one, "f0004.jpg"))).astype(int)
        self.assertLess(np.abs(a - b).max(), 3)                                   # SMAA nạp xong trước frame đầu
        self.assertLessEqual(a[40:200, 40:200].max(), 6)                          # nền vẫn đen


if __name__ == "__main__":
    unittest.main()
