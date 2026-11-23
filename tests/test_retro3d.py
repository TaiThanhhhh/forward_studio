"""Vòng 10 WP-T: look 3D thời 90 (retro90/psx) + nhân vật con vật 3D sinh thủ tục (engines/three/creatures.js) + bối cảnh
meadow/tabletop/street của cảnh `stage`. Python đọc từ vựng thẳng từ JS (một nguồn sự thật); phần JS chạy trong Node
(không WebGL): dựng mọi loài × dáng, tất định, tai/đuôi trễ pha, nhìn theo điểm, đi theo đường, mặt bàn tabletop."""
import json
import os
import re
import shutil
import subprocess
import unittest

from engines import adapter
from tests.test_hybrid import look3d_kinds
from vidlib import textstyle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_SPECIES = {"dog", "dachshund", "cat", "fox", "wolf", "bear", "rabbit", "mouse", "pig", "cow", "horse", "sheep",
                    "chicken", "penguin", "fish", "frog", "turtle", "dino", "kid", "adult"}
REQUIRED_GAITS = {"idle", "walk", "trot", "run", "sniff", "sit", "jump", "wag", "eat", "sleep", "fall"}
REQUIRED_EXPRS = {"neutral", "happy", "shock", "sad", "angry", "sleepy", "sniff"}


def look3d_preset(kind):
    """Các khoá của một preset trong LOOK3D (main.js) — đọc khối `kind: { … },` (có thể nhiều dòng)."""
    with open(os.path.join(ROOT, "engines", "three", "main.js"), encoding="utf-8") as fh:
        body = fh.read().split("const LOOK3D = {", 1)[1].split("\n};", 1)[0]
    m = re.search(rf"^\s{{2}}{kind}: \{{(.*?)\}},\s*$", body, re.M | re.S)
    return dict(re.findall(r"(\w+): ('[^']*'|[\w.]+)", m.group(1))) if m else {}


def node(js):
    r = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", check=True, timeout=180)
    return json.loads(r.stdout.strip().splitlines()[-1])


JS_CTX = """
import * as THREE from './vendor/three/three.module.js';
import * as MO from './lib/motion/motion.js';
import * as PROPS from './engines/three/props.js';
import * as CAST from './engines/three/cast.js';
import * as CR from './engines/three/creatures.js';
import { build } from './engines/three/scenes/stage.js';
const world = new THREE.Group();
const mkctx = (N) => ({ THREE, MO, PROPS, CAST, world, N, fps: 30, job: { font_family: 'sans-serif' }, C: (k) => k,
  toon: () => new THREE.MeshBasicMaterial(), flat: () => new THREE.MeshBasicMaterial(),
  glow: (c, s, p = world) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial()); p.add(m); return m; },
  add: (geo, m, x = 0, y = 0, z = 0, p = world) => {
    const me = new THREE.Mesh(geo, typeof m === 'string' ? new THREE.MeshBasicMaterial() : m);
    me.position.set(x, y, z); p.add(me); return me; },
  group: (p = world, x = 0, y = 0, z = 0) => {
    const g = new THREE.Group(); g.position.set(x, y, z); p.add(g); return g; } });
const r4 = (v) => Math.round(v * 1e4) / 1e4;
"""


class TestLookRetro(unittest.TestCase):
    def test_retro_presets_in_look3d(self):
        kinds = look3d_kinds()
        self.assertTrue({"retro90", "psx"} <= kinds)
        n64, ps1 = look3d_preset("retro90"), look3d_preset("psx")
        for pre in (n64, ps1):
            self.assertEqual(pre.get("mat"), "'gouraud'")              # Gouraud theo đỉnh, không phải Lambert per-fragment
            self.assertEqual(pre.get("ink_px"), "0")                   # thời 90 không có viền
            for k in ("res_div", "color_bits", "dither", "filter", "upscale", "tex_px", "wobble", "affine", "blob"):
                self.assertIn(k, pre)
        self.assertEqual(n64["filter"], "'bilinear'")
        self.assertEqual(ps1["filter"], "'nearest'")
        self.assertEqual(ps1["upscale"], "'nearest'")
        self.assertGreater(float(ps1["res_div"]), float(n64["res_div"]))
        self.assertGreater(float(ps1["wobble"]), 0)                    # PS1 rung đỉnh, N64 không
        self.assertEqual(float(n64["wobble"]), 0)

    def test_shader_is_vertex_lit_and_black_safe(self):
        with open(os.path.join(ROOT, "engines", "three", "main.js"), encoding="utf-8") as fh:
            src = fh.read()
        vs = src.split("const GOURAUD_VS = `", 1)[1].split("`;", 1)[0]
        fs = src.split("const GOURAUD_FS = `", 1)[1].split("`;", 1)[0]
        self.assertIn("uKeyDir", vs)                                    # ánh sáng tính ở vertex shader…
        self.assertNotIn("uKeyDir", fs)                                 # …fragment chỉ nhân màu nội suy
        self.assertIn("vLit", fs)
        for f in ("main.js", "creatures.js", "props.js"):
            with open(os.path.join(ROOT, "engines", "three", f), encoding="utf-8") as fh:
                self.assertNotIn("Math.random(", fh.read(), f)              # tất định: không ngẫu nhiên thật
        q = src.split("const RETRO = ", 1)[1].split("})() : null;", 1)[0]
        self.assertIn("smoothstep(0., 2./lv", q)                        # đen tuyền không bị dither → nền vẫn #000

    def test_style_retro90(self):
        st = textstyle.load_style("retro90-lowpoly-black")
        for k in ("name", "description", "source", "code_engine", "tags", "palette", "not", "pacing", "marks",
                  "transitions", "sfx_pack", "music", "voice_persona", "thumbnail", "flow", "font", "black_min",
                  "voice_tags", "html", "world"):
            self.assertTrue(st.get(k), k)
        self.assertEqual(st["code_engine"], "three")
        self.assertEqual(st["world"]["look3d"], "retro90")
        self.assertTrue(st["flow"]["is_3d"])
        # Darkmode: nền tối (độ sáng RGB thấp, không bắt buộc #000000 tuyệt đối)
        bg = st["palette"]["bg"].lstrip("#")
        self.assertLessEqual(max(int(bg[i:i + 2], 16) for i in (0, 2, 4)), 32)
        self.assertGreaterEqual(float(st["black_min"]), 0.2)
        self.assertTrue({"animal", "pet", "dog", "cat", "nostalgia", "retro", "gaming", "childhood", "nature", "farm",
                         "zoo", "cartoon"} <= set(st["tags"]))
        self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "fonts", st["font"])))


class TestCreatureVocab(unittest.TestCase):
    def test_vocab_read_from_js(self):
        v = adapter.creature_vocab()
        self.assertGreaterEqual(len(v["species"]), 20)
        self.assertTrue(REQUIRED_SPECIES <= set(v["species"]))
        self.assertTrue(REQUIRED_GAITS <= set(v["gaits"]))
        self.assertTrue(REQUIRED_EXPRS <= set(v["exprs"]))
        self.assertGreaterEqual(len(v["exprs"]), 7)
        self.assertTrue({"meadow", "tabletop", "street", "black", "lab", "track"} <= set(v["sets"]))
        for alias, sp in v["aliases"].items():
            self.assertIn(sp, v["species"], alias)
        self.assertNotIn("mouse", v["aliases"])                         # "mouse" = chuột máy tính (icon) — không chiếm

    def test_validate_creature_props(self):
        bad = {"set": "medow", "props": [
            {"id": "d", "type": "creature", "species": "dachsund", "gait": "sniffing", "expr": "hapy", "look": [1, 2]},
            {"id": "p", "type": "puppy", "keys": [{"u": 0.5, "gait": "trott", "expr": "sleepy"}]},
            {"id": "k", "type": "kid", "hair": "mohawk"}]}
        errs = adapter.validate_three("stage", bad)
        txt = "\n".join(errs)
        for want in ("'meadow'", "'dachshund'", "'sniff'", "'happy'", "'trot'", "look là [x, y, z]", "hair 'mohawk'"):
            self.assertIn(want, txt)
        ok = {"set": "meadow", "set_opts": {"seed": 3}, "blob": 0.5, "props": [
            {"type": "dachshund", "gait": "sniff", "expr": "happy", "look": [0.3, 0.2, 0.1]},
            {"type": "creature", "species": "cow", "keys": [{"u": 0.4, "gait": "walk", "look": "camera"}]},
            {"type": "adult", "hair": "bob", "color": {"shirt": "accent"}}, {"type": "flower", "at": [0.3, 0, 0.1]}]}
        self.assertEqual(adapter.stage_creature_errors(ok), [])


@unittest.skipUnless(shutil.which("node"), "cần node")
class TestCreaturesNode(unittest.TestCase):
    def test_every_species_every_gait_builds_and_is_deterministic(self):
        js = JS_CTX + """
        const out = {};
        for (const sp of Object.keys(CR.SPECIES)) for (const gait of CR.GAITS) {
          const ctx = mkctx(40), c = CR.creature(ctx, { species: sp, gait });
          c.bind([{ f: 0 }], null);
          const row = [];
          for (const f of [0, 9, 23, 39]) {
            c.update(f, {}); c.g.updateMatrixWorld(true);
            const b = new THREE.Box3().setFromObject(c.g);
            row.push([b.min.x, b.min.y, b.max.y, b.max.z].map(r4));
          }
          out[sp + ':' + gait] = row; world.remove(c.g);
        }
        console.log(JSON.stringify(out));
        """
        a, b = node(js), node(js)
        self.assertEqual(a, b)                                          # cùng frame → cùng dáng (worker nào cũng vậy)
        self.assertEqual(len(a), len(adapter.creature_vocab()["species"]) * len(adapter.creature_vocab()["gaits"]))
        for k, rows in a.items():
            for r in rows:
                self.assertTrue(all(abs(v) < 50 for v in r), k)
        idle = a["dog:idle"][1]
        self.assertGreater(idle[2], 0.4)                                # chó đứng: cao > 0.4 m
        self.assertGreater(idle[1], -0.06)                              # chân không lún sâu xuống đất
        self.assertLess(a["dog:sleep"][3][2], idle[2] - 0.08)           # nằm ngủ thấp hơn đứng
        self.assertGreater(a["adult:idle"][1][2], 1.5)                  # người lớn ~1.7 m

    def test_follow_through_look_and_path(self):
        js = JS_CTX + """
        const N = 60, ctx = mkctx(N);
        // vẫy đuôi: đốt sau trễ pha đốt trước
        const d = CR.creature(ctx, { species: 'dog', gait: 'wag' }); d.bind([{ f: 0 }], null);
        const t0 = [], t1 = [];
        for (let f = 0; f < N; f++) {
          d.update(f, {}); t0.push(d.joints.tail[0].rotation.y); t1.push(d.joints.tail[1].rotation.y); }
        // nhìn theo điểm: mục tiêu bên +X → cổ quay dương, bên −X → âm
        const look = (x) => {
          const c = CR.creature(mkctx(N), { species: 'dog', gait: 'idle', look: [x, 0.3, 0.3] }); c.bind([{ f: 0 }], null);
          c.update(10, {}); return c.joints.neck.rotation.y + c.joints.headPivot.rotation.y; };
        // đi theo đường: at chạy từ x=-1 → x=+1 → quay mặt +X (≈ +90°), dáng tự chọn đi bộ, chân đổi pha
        const w = CR.creature(mkctx(N), { species: 'dog' });
        const pose = (f) => ({ at: [-1 + 2 * f / (N - 1), 0, 0], sc: [1, 1, 1] });
        w.bind([{ f: 0 }], pose);
        const hips = []; let head = 0, gait = '';
        for (let f = 0; f < N; f++) {
          w.g.position.set(...pose(f).at); w.update(f, {}); hips.push(w.joints.legs[0].hip.rotation.x);
          if (f === 30) head = w.g.children[0].rotation.y;
        }
        const spread = Math.max(...hips) - Math.min(...hips);
        console.log(JSON.stringify({ t0: t0.map(r4), t1: t1.map(r4), lookR: r4(look(1.5)), lookL: r4(look(-1.5)),
          head: r4(head), spread: r4(spread) }));
        """
        o = node(js)
        err = lambda lag: sum(abs(o["t1"][f] / 0.55 - o["t0"][f - lag] / 0.55) for f in range(12, 60))  # noqa: E731
        self.assertLess(min(err(1), err(2)), err(0))                    # đốt 2 = đốt 1 của 1–2 frame trước
        self.assertGreater(o["lookR"], 0.3)
        self.assertLess(o["lookL"], -0.3)
        self.assertAlmostEqual(o["head"], 1.5708, delta=0.2)            # mặt quay theo hướng đi
        self.assertGreater(o["spread"], 0.3)                            # chân bước

    def test_sets_and_tabletop_surface(self):
        js = JS_CTX + """
        const res = {};
        for (const set of ['meadow', 'tabletop', 'street']) {
          const ctx = mkctx(20), w0 = world.children.length;
          const props = [{ id: 'c', type: 'cat', gait: 'sit' }, { id: 'f', type: 'flower', at: [0.3, 0, 0.1] }];
          const s = build(ctx, { set, props });
          s.frame(10);
          res[set] = { y: r4(s.objectOf('c').position.y), n: world.children.length - w0 };
        }
        let err = '';
        try { build(mkctx(10), { set: 'beach', props: [] }); } catch (e) { err = String(e.message); }
        res.err = err;
        console.log(JSON.stringify(res));
        """
        o = node(js)
        self.assertAlmostEqual(o["tabletop"]["y"], 0.76, places=3)     # prop đứng trên mặt bàn (như BASE của lab)
        self.assertEqual(o["meadow"]["y"], 0)
        for s in ("meadow", "tabletop", "street"):
            self.assertGreater(o[s]["n"], 2)                            # bối cảnh + prop đã dựng
        self.assertIn("beach", o["err"])


class TestSheetScript(unittest.TestCase):
    def test_prop_types_include_creatures_and_nature(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("props3d_sheet", os.path.join(ROOT, "scripts", "props3d_sheet.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        types = mod.prop_types()
        for t in ("creature", "flower", "rock", "tree"):
            self.assertIn(t, types)


if __name__ == "__main__":
    unittest.main()
