"""Vòng 10 · WP-H1: look 2D mới (halftone, comic, pixel16, sprite8, silhouette, cutout, lineart), hậu kỳ in/pixel
(post2d.js), nhân vật hoạt hình 2D (rig2d.js ↔ rig2d.py) và 6 style JSON. Phần JS chạy bằng node (không trình duyệt);
ca render thật (tất định, nền đen ≥ black_min, chữ OCR đọc được) cần STUDIO_VISUAL=1 như tests/test_visual.py."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from engines.html import rig2d
from vidlib import textstyle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_LOOKS = ("halftone", "comic", "pixel16", "sprite8", "silhouette", "cutout", "lineart")
NEW_STYLES = {"halftone-print-black": "halftone", "vintage-comic-black": "comic", "pixel16-black": "pixel16",
              "sprite8-black": "sprite8", "ink-silhouette-black": "silhouette", "paper-cutout-black": "cutout"}
VISUAL = unittest.skipUnless(os.environ.get("STUDIO_VISUAL"), "đặt STUDIO_VISUAL=1 để chạy ca engine trình duyệt")
HAS_NODE = unittest.skipUnless(shutil.which("node"), "cần node để chạy bản JS")
RIG = "file:///" + os.path.join(ROOT, "engines", "html", "rig2d.js").replace(os.sep, "/")
POST = "file:///" + os.path.join(ROOT, "engines", "html", "post2d.js").replace(os.sep, "/")


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as fh:
        return fh.read()


def node(code):
    r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", timeout=180)
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout.strip())


class Looks(unittest.TestCase):
    def test_new_looks_in_raw_in_order(self):
        body = re.search(r"const RAW = \{([^}]*)\}", read("engines", "html", "looks.js")).group(1)
        raw = [b.strip() for b in body.split(",")]
        i0 = raw.index(NEW_LOOKS[0])
        self.assertEqual(tuple(raw[i0:i0 + len(NEW_LOOKS)]), NEW_LOOKS)  # giữ đúng thứ tự nối liền nhau trong RAW

    def test_post_tokens_known(self):
        """Look nào bật hậu kỳ in/pixel chỉ dùng khoá post2d.js hiểu; pixel/halftone chữ phải vẽ hoãn (sắc, OCR đọc được)."""
        src = read("engines", "html", "looks.js")
        for look in ("halftone", "comic", "pixel16", "sprite8"):
            body = src[src.index(f"const {look} = {{"):]
            body = body[: body.index("\n};")]
            self.assertIn("deferText: true", body, look)
            self.assertRegex(body, r"(halftone|pixel): \{", look)
        p2 = read("engines", "html", "post2d.js")
        for key in ("opts.pixel", "opts.halftone", "opts.misregister", "opts.paper"):
            self.assertIn(key, p2)

    def test_no_random_or_clock_in_new_code(self):
        for fn in ("rig2d.js", "post2d.js", "looks.js", "core.js"):
            src = read("engines", "html", fn)
            self.assertNotIn("Math.random", src, fn)
            self.assertNotRegex(src, r"Date\.now|performance\.now", fn)

    @HAS_NODE
    def test_pixel_palette_limits(self):
        out = node(f"import {{ pixelPalette }} from '{POST}';"
                   "const b = [[0.97,0.95,0.89],[0.95,0.33,0.29],[0.24,0.55,0.94],[0.98,0.78,0.27]];"
                   "console.log(JSON.stringify([pixelPalette(b, {colors: 48}),"
                   " pixelPalette(b, {colors: 16, ramp: [0.45,1,1.45], greys: 2}),"
                   " pixelPalette(b.concat(b.map(c => c.map(v => v * 0.5))), {colors: 200})]));")
        p48, p16, pmax = out
        self.assertLessEqual(len(p48), 48)
        self.assertLessEqual(len(p16), 16)
        self.assertLessEqual(len(pmax), 64)                           # không bao giờ quá 64 màu
        for pal in out:
            self.assertEqual(pal[0], [0, 0, 0])                        # đen luôn có → nền đen giữ đúng #000


class Rig(unittest.TestCase):
    def test_vocab_read_from_js(self):
        self.assertGreaterEqual(len(rig2d.species()), 14)
        need = {"dog", "cat", "bird", "fish", "rabbit", "bear", "fox", "mouse", "frog", "cow", "pig", "horse", "kid",
                "adult"}
        self.assertTrue(need <= set(rig2d.species()))
        self.assertGreaterEqual(len(rig2d.exprs()), 6)
        acts = {"idle", "walk", "run", "jump", "point", "cheer", "sit", "sniff", "sleep", "eat", "fall"}
        self.assertTrue(acts <= set(rig2d.actions()))
        self.assertTrue(set(rig2d.aliases().values()) <= set(rig2d.species()))

    def test_check_names(self):
        self.assertIsNone(rig2d.check("rig:dog"))
        self.assertIsNone(rig2d.check("rig:puppy:run:happy:left"))
        self.assertIsNone(rig2d.check("rig:kid:wave:curly"))
        self.assertIsNone(rig2d.check("dog"))                           # không phải rig → không kiểm ở đây
        e = rig2d.check("rig:dgo:walk")
        self.assertIn("dog", e)                                         # gợi ý tên gần đúng
        e = rig2d.check("rig:cat:wlak")
        self.assertIn("walk", e)
        self.assertEqual(rig2d.check_args({"action": "run", "expr": "happy"}), [])
        self.assertTrue(rig2d.check_args({"expr": "hapy"}))

    @HAS_NODE
    def test_js_and_python_agree(self):
        js = node(f"import * as R from '{RIG}'; console.log(JSON.stringify({{sp: Object.keys(R.SPECIES), act: R.ACTIONS, "
                  "ex: R.EXPRS, hair: R.HAIRS, al: R.RIG_ALIASES, "
                  "plans: [...new Set(Object.values(R.SPECIES).map(s => s.plan))], "
                  "parse: R.parseRig('rig:puppy:happy:run:left:xx')}));")
        self.assertEqual(js["sp"], rig2d.species())
        self.assertEqual(js["act"], rig2d.actions())
        self.assertEqual(js["ex"], rig2d.exprs())
        self.assertEqual(js["hair"], rig2d.hairs())
        self.assertEqual(js["al"], rig2d.aliases())
        self.assertEqual(set(js["plans"]), set(rig2d.table().values()))
        py = rig2d.parse("rig:puppy:happy:run:left:xx")
        for k in ("species", "action", "expr", "face", "bad"):
            self.assertEqual(js["parse"][k], py[k], k)

    @HAS_NODE
    def test_every_species_action_expr_gives_valid_primitives(self):
        """Mọi loài × hành động × biểu cảm × vài frame: primitive hợp lệ (toạ độ hữu hạn, vai màu đúng), tất định,
        có chuyển động (thở/đi), quay trái = đối xứng gương."""
        out = node(f"""import {{ SPECIES, ACTIONS, EXPRS, rigPrims }} from '{RIG}';
const ROLES = new Set(['ink','dim','hot','cold','accent','bg']); let n = 0, bad = [], still = [];
for (const sp of Object.keys(SPECIES)) for (const a of ACTIONS) {{
  for (const e of EXPRS) for (const f of [0, 13, 47]) {{
    const pr = rigPrims(`rig:${{sp}}:${{a}}:${{e}}`, {{ f, fps: 30, seed: 7 }}); n++;
    for (const p of pr) {{
      const fin = (q) => Number.isFinite(q[0]) && Number.isFinite(q[1]);
      const ok = (p.k === 'circle' ? [p.x, p.y, p.rx ?? p.r, p.ry ?? p.r].every(Number.isFinite)
                                   : p.pts.length >= 2 && p.pts.every(fin))
        && (ROLES.has(p.role) || String(p.role).startsWith('#')) && ['circle','poly','line'].includes(p.k);
      if (!ok) bad.push(sp + ':' + a + ':' + e);
    }}
  }}
  const A = JSON.stringify(rigPrims(`rig:${{sp}}:${{a}}`, {{ f: 5, seed: 3 }}));
  const B = JSON.stringify(rigPrims(`rig:${{sp}}:${{a}}`, {{ f: 23, seed: 3 }}));
  if (A === B) still.push(sp + ':' + a);
}}
const r = rigPrims('rig:dog:walk', {{ f: 9, seed: 2 }}), l = rigPrims('rig:dog:walk:left', {{ f: 9, seed: 2 }});
const mir = r.every((p, i) => p.k === 'circle' ? Math.abs(p.x + l[i].x) < 1e-9
                                              : p.pts.every((q, j) => Math.abs(q[0] + l[i].pts[j][0]) < 1e-9));
const k1 = rigPrims('rig:kid:run:happy', {{ f: 31, seed: 9 }}), k2 = rigPrims('rig:kid:run:happy', {{ f: 31, seed: 9 }});
const det = JSON.stringify(k1) === JSON.stringify(k2);
console.log(JSON.stringify({{ n, bad: bad.slice(0, 5), nbad: bad.length, still, mir, det }}));""")
        self.assertGreater(out["n"], 1000)
        self.assertEqual(out["nbad"], 0, out["bad"])
        self.assertEqual(out["still"], [], "hành động đứng yên giữa hai frame xa nhau (thiếu thở/chu kỳ)")
        self.assertTrue(out["mir"])
        self.assertTrue(out["det"])


class Styles(unittest.TestCase):
    REQUIRED = ("name", "description", "source", "code_engine", "tags", "palette", "not", "pacing", "marks",
                "transitions", "sfx_pack", "music", "voice_persona", "thumbnail", "flow", "font", "black_min", "html",
                "world", "voice_tags")

    def test_six_style_cards_complete(self):
        from vidlib import sfx

        have = set(sfx.available())
        voice_tags = set()
        for pool in json.loads(read("config", "voice.json")).get("pools", {}).values():
            for v in (pool if isinstance(pool, list) else pool.values()):
                if isinstance(v, dict):
                    voice_tags |= set(v.get("tags") or [])
        for sid, look in NEW_STYLES.items():
            st = textstyle.load_style(sid)
            for k in self.REQUIRED:
                self.assertTrue(st.get(k), f"{sid}: thiếu {k}")
            self.assertEqual(st["code_engine"], "html", sid)
            self.assertEqual(st["html"]["look"], look, sid)
            self.assertEqual(st["palette"]["bg"].lower(), "#000000", sid)
            self.assertEqual(st["html"]["palette"]["bg"].lower(), "#000000", sid)
            self.assertEqual(st["world"]["bg"].lower(), "#000000", sid)
            self.assertTrue(st["world"].get("look3d"), sid)
            self.assertGreaterEqual(float(st["black_min"]), 0.4, sid)
            self.assertGreaterEqual(len(st["tags"]), 5, sid)
            self.assertGreaterEqual(len(st["not"]), 3, sid)
            for k in ("medium", "look", "motion"):
                self.assertTrue(st["flow"].get(k), f"{sid}: flow.{k}")
            for f in {st["font"], st["html"]["font"], st["html"].get("mono") or st["font"]}:
                self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "fonts", f)), f"{sid}: {f}")
            for cue, name in st["sfx_pack"].items():
                self.assertIn(name, have, f"{sid}: {cue}→{name}")
            odd = set(st["voice_tags"]) - voice_tags
            self.assertFalse(odd, f"{sid}: voice_tags lạ {odd}")

    def test_new_fonts_have_licence(self):
        fonts = (("PressStart2P-Regular.ttf", "OFL-pressstart2p.txt"), ("PixelifySans-Variable.ttf", "OFL-pixelifysans.txt"))
        for f, lic in fonts:
            self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "fonts", f)), f)
            self.assertIn("SIL Open Font License", read("assets", "fonts", lic))


class Render(unittest.TestCase):
    """Render thật trong Edge headless: mỗi style mới một beat có chữ + một cảnh nhân vật."""

    def _render(self, style, scene, params, frames, only, sub):
        from engines import adapter

        work = tempfile.mkdtemp(prefix="l2d-", dir=os.path.join(ROOT, "qa"))
        self.addCleanup(shutil.rmtree, work, True)
        spec = adapter.ShotSpec(sid="T", engine="html", scene=scene, params=params, frames=frames, fps=30, style=style,
                                work=work)
        job = adapter.get("html").job(spec)
        d = os.path.join(work, sub)
        adapter.get("html").render(job, d, only, log=lambda *a: None, workers=2)
        return d, job

    @VISUAL
    def test_deterministic_black_and_moving(self):
        import numpy as np
        from PIL import Image

        params = {"title": "Who runs faster?", "actors": [
            {"id": "d", "icon": "rig:dog:run:happy", "x": 0.3, "y": 0.55, "size": 300, "keys": [{"u": 1, "x": 0.7}]},
            {"id": "k", "icon": "rig:kid:cheer", "x": 0.68, "y": 0.62, "size": 320}],
            "labels": [{"text": "Fast dog", "of": "d", "u": 0.1}]}
        for style in NEW_STYLES:
            with self.subTest(style=style):
                full, job = self._render(style, "scene", params, 24, None, "all")
                one, _ = self._render(style, "scene", params, 24, [17], "one")
                a = np.asarray(Image.open(os.path.join(full, "f0017.jpg"))).astype(int)
                b = np.asarray(Image.open(os.path.join(one, "f0017.jpg"))).astype(int)
                self.assertLess(np.abs(a - b).max(), 3)                    # worker nào cũng ra cùng ảnh
                fr = [np.asarray(Image.open(os.path.join(full, f"f{f:04d}.jpg")).convert("L").resize((96, 170))).astype(int)
                      for f in range(24)]
                run, best = 0, 0
                for x, y in zip(fr, fr[1:]):
                    run = run + 1 if np.abs(x - y).mean() < 0.02 else 0
                    best = max(best, run)
                self.assertLess(best + 1, 4, "đứng yên ≥ 4 frame")
                lum = a.mean(axis=2)
                need = float(textstyle.load_style(style)["black_min"])
                self.assertGreaterEqual(float((lum < 26).mean()), need, f"{style}: nền đen < black_min")

    @VISUAL
    def test_ocr_reads_text_in_every_look(self):
        from engines import adapter
        from vidlib import ocr

        if not ocr.available():
            self.skipTest("không có tesseract")
        params = {"title": "Cooling curve", "left": {"icon": "rig:cat", "label": "Cat", "value": 38, "unit": "C"},
                  "right": {"icon": "rig:dog", "label": "Dog", "value": 39, "unit": "C"}, "result": "Dogs run warmer"}
        for style in NEW_STYLES:
            with self.subTest(style=style):
                _, job = self._render(style, "compare", params, 60, [59], "f")
                crops = adapter.get("html").text_crops(job, [59])
                got = {}
                for _f, want, crop, _tex in crops:
                    txt, _c = ocr.read(crop, psm=7)
                    got[want] = ocr.norm(txt or "")
                for want in ("Cooling curve", "Dogs run warmer"):
                    hits = [k for k in got if ocr.norm(k) == ocr.norm(want)]
                    self.assertTrue(hits, f"{style}: không có khung chữ '{want}'")
                    self.assertIn(ocr.norm(want), got[hits[0]], f"{style}: OCR đọc '{got[hits[0]]}'")


if __name__ == "__main__":
    unittest.main()
