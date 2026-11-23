# ruff: noqa: E501 — harness JS nhúng nguyên khối (dòng dài là mã JS, không phải Python)
"""Vòng 10 · WP-H2: bố cục/beat mới của engine html, chuyển động do dữ liệu lái, chiều sâu 2D của `scene`.

Phần Python: LAYOUTS ≥ 5/beat, validate, chọn bố cục theo dữ liệu. Phần JS chạy beats.js trong Node với một canvas giả
ghi lại mọi lệnh vẽ (không cần trình duyệt): tất định, số biểu tượng/nhịp đúng dữ liệu, móc verb của lib/motion.
"""
import json
import os
import re
import shutil
import subprocess
import unittest

from engines import html
from vidlib import codeshot
from vidlib.common import ROOT


def _read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as fh:
        return fh.read()


DEMO = json.loads(_read("engines", "html", "demo.json"))


class TestLayoutsAndValidate(unittest.TestCase):
    def test_every_beat_has_five_layouts_with_brief_help(self):
        for beat in ("title", "counter", "compare", "fact", "process"):
            self.assertGreaterEqual(len(html.LAYOUTS[beat]), 5, beat)
        for beat, opts in html.LAYOUTS.items():
            self.assertEqual(set(opts), set(html.LAYOUT_HELP[beat]), beat)
            self.assertEqual(len(set(opts)), len(opts), beat)

    def test_js_dispatch_covers_every_layout(self):
        src = _read("engines", "html", "beats.js")
        body = src[src.index("const LAYOUT10 = {"): src.index("const alt10")]
        js10 = {b: set(re.findall(r"(\w+): \[\w+,", blk)) for b, blk in re.findall(r"(\w+): \{(.*?)\},?\n", body, re.S)}
        for beat, opts in html.LAYOUTS.items():
            fn = src[src.index(f"function {beat}(c0, P) {{"):]
            fn = fn[: fn.index("\n}\n")]
            old = set(re.findall(r"P\.layout === '(\w+)'", fn))
            missing = set(opts[1:]) - old - js10.get(beat, set())
            self.assertFalse(missing, f"{beat}: bố cục không có hàm vẽ: {missing}")

    def test_new_beats_listed_and_demo_valid(self):
        for b in ("units", "timeline", "split", "meter"):
            self.assertIn(b, html.BEATS)
            self.assertIn(b, html.PARAMS)
            self.assertIn(b, codeshot.scenes("html"))
        for key, params in DEMO.items():
            if key.startswith("_"):
                continue
            beat = key.split("__")[0]
            self.assertEqual(html.validate(beat, params), [], key)
            if "__" in key and key.split("__")[1] in html.LAYOUTS.get(beat, ()):
                self.assertEqual(params.get("layout"), key.split("__")[1], key)

    def test_vocab_read_from_js(self):
        self.assertEqual(set(html.meter_kinds()), {"ecg", "battery", "tank", "thermo", "dial"})
        self.assertIn("pulse", html.split_actions())
        self.assertIn("count", html.split_actions())

    def test_bad_data_gives_vietnamese_errors_with_hints(self):
        cases = [
            ("meter", {"kind": "radar", "value": 3}, "ecg"),
            ("meter", {"kind": "ecg", "value": 900}, "20..300"),
            ("meter", {"kind": "tank"}, "value"),
            ("split", {"a": {"action": "pulse"}, "b": {"action": "fill", "value": 3}}, "rate"),
            ("split", {"a": {"action": "dance", "rate": 3}, "b": {"rate": 60}}, "dance"),
            ("timeline", {"events": [{"t": 1, "label": "a"}]}, "2–8"),
            ("timeline", {"events": [{"t": 1, "label": "a"}, {"t": "x", "label": "b"}]}, "t_label"),
            ("units", {"groups": [{"label": "a", "value": -2}]}, "≥ 0"),
            ("units", {"groups": [{"label": "a", "value": 100000, "icon": "person"}], "per": 1}, "per"),
            ("compare", {"left": {"value": 0}, "right": {"value": 4}, "layout": "overlay"}, "overlay"),
            ("process", {"steps": [{"label": "a"}, {"label": "b"}], "layout": "loop"}, "loop"),
            ("counter", {"to": 5000, "layout": "units", "per": 1}, "per"),
            ("scene", {"actors": [{"id": "a", "icon": "ball", "z": 40}]}, "-0.85..20"),
            ("scene", {"actors": [{"id": "a", "icon": "ball"}], "camera": [{"u": 2}]}, "0..1"),
            ("scene", {"actors": [{"id": "a", "icon": "ball"}], "depth": {"blurry": 1}}, "blurry"),
        ]
        for beat, params, want in cases:
            errs = html.validate(beat, params)
            self.assertTrue(errs, f"{beat} {params}")
            self.assertTrue(any(want in e for e in errs), f"{beat}: {errs}")

    def test_scene_verbs_checked_by_lib_motion_when_available(self):
        from lib import motion  # noqa: PLC0415
        if not callable(getattr(motion, "verb_errors", None)):
            self.skipTest("lib/motion chưa có verb (WP-M)")
        ok = {"actors": [{"id": "h", "icon": "heart", "do": [{"u": 0, "verb": "heartbeat", "args": {"bpm": 150}}]}]}
        self.assertEqual(html.validate("scene", ok), [])
        bad = {"actors": [{"id": "h", "icon": "heart", "keys": [{"u": 0.2, "verb": "hartbeat"}]}]}
        self.assertTrue(any("heartbeat" in e for e in html.validate("scene", bad)))

    def test_rig_names_follow_rig2d_js(self):
        if html.rig_vocab() is None:
            self.skipTest("chưa có engines/html/rig2d.js (WP-H1)")
        self.assertIsNone(html.check_icon("rig:dog:walk:happy"))
        self.assertIsNone(html.check_icon("rig:dachshund"))
        self.assertTrue(html.check_icon("rig:dragon"))
        self.assertTrue(html.check_icon("rig:dog:fly"))
        sc = {"actors": [{"id": "d", "icon": "rig:dog", "action": "walk", "keys": [{"u": 0.5, "action": "zoom"}]}]}
        self.assertTrue(any("zoom" in e for e in html.validate("scene", sc)))

    def test_layout_fit_and_rotation_skip_unfit_layouts(self):
        zero = {"left": {"value": 0}, "right": {"value": 3}}
        self.assertFalse(html.layout_fits("compare", "overlay", zero))
        self.assertTrue(html.layout_fits("compare", "race", zero))
        self.assertTrue(html.layout_fits("compare", "bars", zero))
        for seed in range(40):
            used = {}
            picks = [html.pick_layout("compare", f"v{seed}", used, zero) for _ in range(6)]
            self.assertNotIn("overlay", picks)
            self.assertEqual(len(set(picks)), 6)           # 6 bố cục hợp → 6 shot khác nhau
        used = {}
        two = [html.pick_layout("process", "s", used, {"steps": [{"label": "a"}, {"label": "b"}]}) for _ in range(4)]
        self.assertNotIn("loop", two)
        self.assertIsNotNone(html.pick_layout("title", "s", {}))   # gọi kiểu cũ (không params) vẫn chạy

    def test_per_unit_matches_isotype_rules(self):
        self.assertEqual(html.per_unit([23]), 1)
        self.assertEqual(html.per_unit([157]), 2)
        self.assertEqual(html.per_unit([1000]), 10)
        self.assertEqual(html.per_unit([1.33, 1.5]), 0.1)
        self.assertEqual(html.per_unit([84.5]), 1)
        self.assertEqual(html.per_unit([5], given=0.5), 0.5)


HARNESS = r"""
import * as B from './engines/html/beats.js';
const demo = JSON.parse(process.argv[1] ? '{}' : '{}');
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const EASE = { out: (t) => 1 - Math.pow(1 - clamp(t), 3), in: (t) => Math.pow(clamp(t), 3), smooth, linear: clamp,
  back: (t, s = 1.7) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; }, spring: (t) => (t <= 0 ? 0 : t >= 1 ? 1 : 1 - Math.exp(-6 * t) * Math.cos(9 * t)) };
EASE.bounce = (t) => EASE.back(t, 1.56); EASE.dead = EASE.out; EASE.snap = smooth; EASE.expo = EASE.out;
const hash = (a, b = 0, c = 0) => { let h = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263) + Math.imul(c | 0, 2147483647)) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16; return (h >>> 0) / 4294967296; };
const strSeed = (s) => { let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h | 0; };
const fmtNum = (v, d = 0) => Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
function makeC(f, N, P, log, MO) {
  const rec = (k) => (...a) => { log.push([k, ...a.map((x) => (typeof x === 'function' ? 'fn' : x))]); };
  const g = new Proxy({}, { get: (o, k) => (k in o ? o[k] : rec('g.' + String(k))), set: (o, k, v) => { log.push(['set', k, v]); o[k] = v; return true; } });
  const box = (s, x, y, o = {}) => { const w = String(s ?? '').length * (o.size || 80) * 0.5; return { x0: x - w / 2, y0: y - (o.size || 80), x1: x + w / 2, y1: y + 10, h: o.size || 80, lines: 1 }; };
  const K = { header: (c, h, k) => { log.push(['header', h.title, k]); return 480; }, tag: (c, s, x, y, k) => { log.push(['tag', s, x, y, k]); return k > 0 ? box(s, x, y) : null; },
    label: (c, s, x, y, k, o) => { log.push(['label', s, x, y, k]); return box(s, x, y, o); }, arrow: rec('arrow'), ring: rec('ring'), ground: rec('ground'), halo: rec('halo'), bar: rec('bar') };
  return { g, W: 1080, H: 1920, N, FPS: 30, f, fs: f, t: f / 30, u: f / Math.max(1, N - 1), pal: { bg: '#000000', ink: '#ffffff' }, L: { look: 'flat', pen: { fill: true }, type: { align: 'center' } }, P,
    A: { x0: 84, x1: 996, top: 240, bottom: 1516, cx: 540, xr: () => 930 }, E: smooth, EASE, MO, clamp, lerp, hash, noise: (a, b, c) => hash(a, b, c) * 2 - 1, strSeed,
    col: () => '#ffffff', shade: (x) => x, mix: () => '#808080', TAU: Math.PI * 2, K, media: { draw: rec('media') },
    draw: (p, o) => log.push(['draw', JSON.stringify(p).length, o && o.x, o && o.y, o && o.s, o && o.alpha]),
    text: (s, x, y, o = {}) => { if ((o.k ?? 1) > 0) log.push(['text', s, Math.round(x), Math.round(y), o.quiet || false]); return box(s, x, y, o); },
    icon: (n, o = {}) => log.push(['icon', typeof n === 'string' ? n : 'parts', o.x, o.y, o.s, o.sx, o.alpha, o.args && o.args.face]),
    enter: (k, b, fn) => { if (k > 0) fn(k); }, fmtNum, k: (f0, dur) => clamp((f + 9 - f0) / Math.max(1, dur)) };
}
export function run(scene, P, N, frames, MO = { M: { smooth } }) {
  const c0 = makeC(0, N, P, [], MO), S = B.BEATS[scene](c0, P), logs = {};
  for (const f of frames) { const log = []; S.draw(makeC(f, N, P, log, MO)); logs[f] = log; }
  return { cues: S.cues, texts: S.texts, logs };
}
"""


@unittest.skipUnless(shutil.which("node"), "cần node")
class TestBeatsInNode(unittest.TestCase):
    """beats.js không import gì → chạy thẳng trong Node với canvas giả ghi lệnh vẽ."""

    def node(self, body):
        code = HARNESS + "\nconst out = {};\n" + body + "\nconsole.log(JSON.stringify(out));"
        r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_every_beat_and_layout_draws_deterministically(self):
        keys = [k for k in DEMO if not k.startswith("_")]
        out = self.node(
            f"const D = {json.dumps(DEMO)};\n"
            "for (const k of " + json.dumps(keys) + ") {\n"
            "  const sc = k.split('__')[0], fr = [0, 13, 45, 89, 119, -5, 130];\n"
            "  const a = run(sc, D[k], 120, fr), b = run(sc, JSON.parse(JSON.stringify(D[k])), 120, fr);\n"
            "  out[k] = { same: JSON.stringify(a.logs) === JSON.stringify(b.logs), n: a.logs[89].length,\n"
            "    texts: a.texts.every((t) => typeof t === 'string' && t.length > 0),\n"
            "    cues: a.cues.every((q) => Number.isFinite(q.f) && typeof q.name === 'string') };\n"
            "}")
        for k, v in out.items():
            self.assertTrue(v["same"], f"{k}: hai lần vẽ cùng frame khác nhau (không tất định)")
            self.assertGreaterEqual(v["n"], 3, f"{k}: frame 89 gần như trống")
            self.assertTrue(v["texts"] and v["cues"], k)

    def test_no_random_or_clock_in_beats(self):
        src = _read("engines", "html", "beats.js")
        self.assertNotIn("Math.random", src)
        self.assertNotIn("Date.now", src)
        self.assertNotIn("performance.now", src)

    def test_ecg_and_split_beats_follow_real_bpm(self):
        out = self.node(
            "const e = run('meter', { kind: 'ecg', value: 120 }, 150, [0]);\n"
            "out.ecg = e.cues.filter((q) => q.name === 'heartbeat').map((q) => q.f);\n"
            "const s = run('split', { a: { action: 'pulse', rate: 60 }, b: { action: 'pulse', rate: 150 } }, 120, [0]);\n"
            "out.split = s.cues.map((q) => q.f);\n"
            "const r = run('meter', { kind: 'ecg', from: 70, value: 170, land: 0.9 }, 180, [0]);\n"
            "out.ramp = r.cues.map((q) => q.f);")
        gaps = [b - a for a, b in zip(out["ecg"], out["ecg"][1:])]
        self.assertGreaterEqual(len(out["ecg"]), 9)                     # 120 BPM × 5 s = 10 nhịp
        self.assertTrue(all(abs(g - 15) <= 1 for g in gaps), gaps)      # 30 fps · 60/120 s = 15 frame/nhịp
        self.assertGreaterEqual(len(out["split"]), 4 + 9)               # 60 BPM: 4 nhịp · 150 BPM: 10 nhịp/4 s
        rg = [b - a for a, b in zip(out["ramp"], out["ramp"][1:])]
        self.assertGreater(rg[0], rg[-1] + 4)                           # nhịp nhanh dần theo from → value

    def test_isotype_draws_the_real_count(self):
        out = self.node(
            "const a = run('counter', { to: 23, icon: 'cup', layout: 'units' }, 90, [89]);\n"
            "out.cups = a.logs[89].filter((x) => x[0] === 'icon' && x[1] === 'cup').length;\n"
            "const b = run('compare', { layout: 'units', left: { value: 25, icon: 'cube' }, right: { value: 77, icon: 'cube' } }, 90, [89]);\n"
            "out.cubes = b.logs[89].filter((x) => x[0] === 'icon' && x[1] === 'cube').length;\n"
            "const u = run('units', { groups: [{ value: 3000, icon: 'person' }] }, 90, [89]);\n"
            "out.people = u.logs[89].filter((x) => x[0] === 'icon' && x[1] === 'person').length;")
        self.assertEqual(out["cups"], 23)                     # 23 cốc thật (không có chú giải khi per = 1)
        self.assertEqual(out["cubes"], 25 + 77 + 1)           # hai nhóm + biểu tượng chú giải "= 1"
        self.assertEqual(out["people"], 120 + 1)              # beat units: trần 120 → per 25 → 120 biểu tượng + chú giải

    def test_race_winner_reaches_finish_at_land(self):
        out = self.node(
            "const P = { layout: 'race', land: 0.5, left: { value: 10, icon: 'runner' }, right: { value: 5, icon: 'bike' } };\n"
            "const a = run('compare', P, 100, [50, 99]);\n"
            "const ys = (f) => Object.fromEntries(a.logs[f].filter((x) => x[0] === 'icon').map((x) => [x[1], x[3]]));\n"
            "out.y50 = ys(50); out.y99 = ys(99);")
        self.assertGreater(out["y50"]["runner"], out["y50"]["bike"] + 100)  # người thắng gần camera hơn (thấp hơn)
        self.assertAlmostEqual(out["y50"]["runner"], out["y99"]["runner"], delta=5)

    def test_scene_without_depth_is_unchanged_and_depth_uses_filters(self):
        out = self.node(
            f"const D = {json.dumps(DEMO['scene'])}, Z = {json.dumps(DEMO['scene__depth'])};\n"
            "const a = run('scene', D, 90, [45]), b = run('scene', Z, 90, [10, 45]);\n"
            "const filt = (l) => l.filter((x) => x[0] === 'set' && x[1] === 'filter' && x[2] !== 'none').length;\n"
            "out.plain = filt(a.logs[45]); out.deep = filt(b.logs[45]);\n"
            "const xs = (l) => Object.fromEntries(l.filter((x) => x[0] === 'icon').map((x, i) => [i, x[2]]));\n"
            "out.x10 = xs(b.logs[10]); out.x45 = xs(b.logs[45]);")
        self.assertEqual(out["plain"], 0)            # cảnh cũ không có z/camera → không lớp lọc nào (vẽ như cũ)
        self.assertGreater(out["deep"], 5)           # DOF + không khí theo độ sâu

    def test_verb_hook_uses_lib_motion_play_or_fallback(self):
        out = self.node(
            "const P = { actors: [{ id: 'h', icon: 'heart', size: 200, do: [{ u: 0, verb: 'heartbeat', args: { bpm: 120 } }] }] };\n"
            "const fake = { M: { smooth }, play: () => ({ x: 0, y: 0, z: 0, sx: 1.5, sy: 1.5, rot: 0, alpha: 1, glow: 0, blur: 0, reveal: 1 }),\n"
            "  canvasDelta: (d) => ({ dx: 0, dy: 0, dz: 0, sx: d.sx, sy: d.sy, rot: 0, alpha: 1, glow: 0, blur: 0, reveal: 1 }) };\n"
            "out.lib = run('scene', P, 60, [7], fake).logs[7].find((x) => x[0] === 'icon')[5];\n"
            "const fb = run('scene', P, 60, [0, 1, 2, 3, 4, 5, 6, 7, 8, 15]);\n"
            "out.fb = Object.values(fb.logs).map((l) => l.find((x) => x[0] === 'icon')[5]);\n"
            "const real = await import('./lib/motion/motion.js');\n"
            "out.real = typeof real.play === 'function' ? run('scene', P, 60, [0, 1], { ...real, M: real.M }).logs[1].find((x) => x[0] === 'icon')[5] : null;")
        self.assertEqual(out["lib"], 1.5)                         # lib/motion có play → dùng đúng delta của nó
        self.assertGreater(max(out["fb"]), 1.05)                  # dự phòng: tim phồng theo nhịp
        if out["real"] is not None:
            self.assertNotEqual(out["real"], 1)                   # lib/motion thật (WP-M): heartbeat đổi cỡ

    def test_rig_actor_faces_where_it_walks(self):
        out = self.node(
            "const P = { actors: [{ id: 'd', icon: 'rig:dog', x: 0.8, keys: [{ u: 1, x: 0.2 }], action: 'walk' }] };\n"
            "out.face = run('scene', P, 60, [30]).logs[30].find((x) => x[0] === 'icon')[7];")
        self.assertEqual(out["face"], "left")


if __name__ == "__main__":
    unittest.main()
