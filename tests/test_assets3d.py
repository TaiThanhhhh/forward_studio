"""Vòng 10 — WP-A: Kho tài sản thư viện 3D glTF/GLB (CC0) + icon SVG (MIT).
Kiểm tra: nạp index config/assets3d.json, search, lookup, check() xanh (giấy phép hợp lệ, SHA khớp),
prop_errors báo lỗi có gợi ý khi sai tên model hoặc sai tên anim, userassets giải tên model: và svg: thư viện."""

import json
import os
import shutil
import subprocess
import unittest

from engines import adapter, html
from vidlib import assets3d as A
from vidlib import userassets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def node(code):
    r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout.strip())


class Assets3DIndexTests(unittest.TestCase):
    def test_index_loads_and_summary(self):
        idx = A.index()
        self.assertIn("packs", idx)
        self.assertIn("models", idx)
        self.assertGreaterEqual(len(A.models()), 150)
        s = A.summary()
        self.assertEqual(s["models"], len(A.models()))
        self.assertGreaterEqual(s["animated"], 6)
        self.assertGreaterEqual(s["svg"], 500)

    def test_check_is_green(self):
        issues = A.check(files=True)
        errs = [m for lvl, m in issues if lvl == "err"]
        self.assertEqual(errs, [], f"assets3d.check() có lỗi: {errs}")
        ok_lic = set(A.allowed_licenses())
        for pid, p in A.packs().items():
            self.assertIn(p.get("license"), ok_lic, f"gói {pid} sai giấy phép")

    def test_search_and_lookup(self):
        hits = A.search("knight", limit=5, kind="3d")
        self.assertTrue(hits)
        self.assertEqual(hits[0][1], "knight")
        # Khớp số nhiều / dạng gốc (berries -> berry, burgers -> burger)
        hits_pl = A.search("burgers", limit=5, kind="3d")
        self.assertTrue(any("burger" in h[1] for h in hits_pl))
        # Tìm SVG
        svg_hits = A.search("heart", limit=5, kind="svg")
        self.assertTrue(svg_hits)
        # lookup tên chính xác, bí danh, từ khoá
        n1, e1 = A.lookup("knight")
        self.assertEqual(n1, "knight")
        self.assertIn("anims", e1)
        for alias, target in A.aliases().items():
            na, _ = A.lookup(alias)
            expected = alias if alias in A.models() else target
            self.assertEqual(na, expected)
        # Tên sai trả về (None, danh sách gợi ý)
        n_bad, sugg = A.lookup("knigth")
        self.assertIsNone(n_bad)
        self.assertIn("knight", sugg)

    def test_prop_errors_with_suggestions(self):
        # Tên model đúng + anim đúng -> không lỗi
        self.assertEqual(A.prop_errors({"type": "model:knight", "anim": "walk"}), [])
        # Sai tên model -> báo lỗi kèm gợi ý gần nhất
        e_model = A.prop_errors({"type": "model:knigth"})
        self.assertEqual(len(e_model), 1)
        self.assertIn("knight", e_model[0])
        self.assertIn("assets search", e_model[0])
        # Sai tên anim trên model có anim -> báo lỗi kèm danh sách anim có sẵn
        e_anim = A.prop_errors({"type": "model:knight", "anim": "fly_to_moon"})
        self.assertEqual(len(e_anim), 1)
        self.assertIn("fly_to_moon", e_anim[0])
        self.assertIn("Idle", e_anim[0])
        # Gắn anim cho model tĩnh không có animation -> báo lỗi bỏ anim
        static_name = next(n for n, e in A.models().items() if not e.get("anims"))
        e_static = A.prop_errors({"type": f"model:{static_name}", "anim": "walk"})
        self.assertEqual(len(e_static), 1)
        self.assertIn("không có animation", e_static[0])
        # Sai kiểu tham số số
        e_num = A.prop_errors({"type": "model:knight", "h": "tall"})
        self.assertTrue(any("h phải là số" in x for x in e_num))

    def test_userassets_resolves_model_and_library_svg(self):
        # 1. three.js prop model:<tên>
        p3 = {"props": [{"id": "k", "type": "model:knight", "anim": "walk"}]}
        r3 = userassets.resolve(p3, "three")
        prop = r3["props"][0]
        self.assertTrue(prop["model_url"].startswith("/assets/lib/3d/"))
        self.assertEqual(prop["model"]["name"], "knight")
        self.assertIn("Idle", prop["model"]["anims"])
        self.assertEqual(adapter.validate_three("stage", p3), [])
        self.assertTrue(adapter.validate_three("stage", {"props": [{"id": "k", "type": "model:knigth"}]}))

        # 2. html + three svg:<tên> từ kho thư viện
        svg_name = next(iter((A.svg_index().get("icons") or {}).keys()))
        p2 = {"actors": [{"id": "a", "icon": f"svg:{svg_name}"}]}
        r2 = userassets.resolve(p2, "html")
        self.assertIsInstance(r2["actors"][0]["icon"], dict)
        self.assertTrue(r2["actors"][0]["icon"]["parts"])
        self.assertEqual(html.validate("scene", p2), [])

        # 3. three svg:<tên> từ kho thư viện -> ép khối svgicon
        p3_svg = {"props": [{"id": "s", "type": f"svg:{svg_name}"}]}
        r3_svg = userassets.resolve(p3_svg, "three")
        self.assertEqual(r3_svg["props"][0]["type"], "svgicon")
        self.assertTrue(r3_svg["props"][0]["icon_parts"])

        # 4. license_notes ghi nhận cả model và svg thư viện
        notes = userassets.license_notes({
            "props": [{"type": "model:knight"}, {"type": f"svg:{svg_name}"}]
        })
        self.assertEqual([k for k, _, _ in notes], ["model", "svg"])
        self.assertTrue(all(lic for _, _, lic in notes))

    @unittest.skipUnless(shutil.which("node"), "cần node")
    def test_anim_norm_and_match_parity_with_js(self):
        out = node("""
        import { animNorm, pickName } from './engines/three/models.js';
        const names = ['Rig|Walk_Forward', 'Rig|Idle_A', 'Jump_Start'];
        console.log(JSON.stringify({
          norm: animNorm('Rig|Walk_Forward'),
          walk: pickName(names, 'walk'),
          idle: pickName(names, 'idle'),
          none: pickName(names, 'swim')
        }));
        """)
        names = ["Rig|Walk_Forward", "Rig|Idle_A", "Jump_Start"]
        self.assertEqual(out["norm"], A.anim_norm("Rig|Walk_Forward"))
        self.assertEqual(out["walk"], A.anim_match(names, "walk"))
        self.assertEqual(out["idle"], A.anim_match(names, "idle"))
        self.assertIsNone(out["none"])
        self.assertIsNone(A.anim_match(names, "swim"))


if __name__ == "__main__":
    unittest.main()
