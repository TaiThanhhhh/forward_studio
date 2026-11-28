# ruff: noqa: E501 — chuỗi JS nhúng chạy bằng node, giữ nguyên dòng cho dễ đọc
"""Vòng 22: rủi ro chính sách YouTube (policy), đạo cụ chi tiết (icons_detail), người tả thực (rig_human: đi/chạy/đạp xe,
x-ray cột sống/cơ/nhiên liệu), bối cảnh đêm (backdrops), kính lúp + freeze của beat scene, profile explainer (nhịp,
không punch-in tự chèn, kiểu bay êm), dòng 'not medical advice' khi upload video sức khoẻ."""
import json
import shutil
import subprocess
import unittest

from engines import html
from vidlib import policy, spine, timeline, ytupload
from vidlib.common import ROOT, duration_profile

NODE = shutil.which("node")


def _node(code):
    r = subprocess.run([NODE, "--input-type=module", "-e", code], capture_output=True, text=True, cwd=ROOT, timeout=90)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _sb(**kw):
    sb = {"title": "Test", "topic": "t", "universe": "A", "shots": [], "publish": {"youtube_shorts": {"titles": ["Test"], "description": "d"}}}
    sb.update(kw)
    return sb


def _scene(icons, backdrop=None, organs=None):
    p = {"actors": [{"id": f"a{i}", "icon": ic, **({"organs": organs} if organs else {})} for i, ic in enumerate(icons)]}
    if backdrop:
        p["backdrop"] = backdrop
    return {"id": "C01", "mode": "code", "vo": "x", "code": {"engine": "html", "scene": "scene", "params": p}}


class TestPolicy(unittest.TestCase):
    def test_spoken_numbers(self):
        got = policy.word_numbers("More than forty percent, one point five. Point one plus point two, twenty-four frames, a hundred and ten")
        for v in (40, 1.5, 0.1, 0.2, 24, 110):
            self.assertIn(float(v), got)

    def test_frame_key_includes_backdrop_and_organs(self):
        a = policy.frame_key(_scene(["rig:athlete:run"], "city"))
        b = policy.frame_key(_scene(["rig:athlete:run"], "track"))
        c = policy.frame_key(_scene(["rig:athlete:run"], "city", ["fuel", "spine"]))
        self.assertFalse(policy.same_frame(a, b))
        self.assertFalse(policy.same_frame(a, c))
        self.assertTrue(policy.same_frame(a, policy.frame_key(_scene(["rig:athlete:run:happy"], "city"))))

    def test_repetition_against_history(self):
        tmpl = {"id": "C02", "mode": "code", "vo": "x", "code": {"engine": "html", "scene": "xray_cutaway", "params": {"shell_icon": "person"}}}
        hist = [("old-video", {"shots": [tmpl]})]
        me = _sb(shots=[dict(tmpl, id="C01"), _scene(["laptop", "chip"], "office")])
        rep = policy.repetition(me, hist=hist)
        self.assertEqual(rep["n"], 2)
        self.assertEqual([r["sid"] for r in rep["rows"]], ["C01"])
        iss = policy.lint(me, hist=hist)
        self.assertTrue(any(i["code"] == "repeat" and i["level"] == "error" for i in iss))

    def test_persona_spam_kids_promise(self):
        sb = _sb(shots=[{"id": "C01", "vo": "As a doctor, you should take 400 mg every morning.", "mode": "code",
                         "code": {"engine": "html", "scene": "scene", "params": {}}}],
                 publish={"youtube_shorts": {"titles": ["5 Facts in 30 Seconds"], "description": "Comment YES if you agree! For kids!",
                                             "hashtags": [f"h{i}" for i in range(20)]}})
        codes = {(i["code"], i["level"]) for i in policy.lint(sb, hist=[])}
        for want in [("persona", "error"), ("persona", "warn"), ("spam", "error"), ("kids", "warn"), ("promise", "warn")]:
            self.assertIn(want, codes)

    def test_disclaimer_added_to_health_upload(self):
        sb = _sb(shots=[{"id": "C01", "vo": "Your muscles and heart.", "mode": "code", "code": {"scene": "scene", "params": {}}}])
        body = ytupload.build_payload(sb)["body"]
        self.assertIn("not medical advice", body["snippet"]["description"].lower())
        self.assertFalse(body["status"]["selfDeclaredMadeForKids"])


class TestGlyphLint(unittest.TestCase):
    def test_missing_glyph_is_error_before_render(self):
        from vidlib import linter
        sb = {"style": "pixel16-black", "shots": [{"id": "C01", "code": {"engine": "html", "scene": "scene", "params": {
            "labels": [{"text": "NOISE → SCENE"}, {"text": "PLAIN TEXT"}], "lenses": [{"title": "ZOOM"}]}}}]}
        iss = linter.lint_glyphs(sb)
        self.assertEqual(len(iss), 1)
        self.assertEqual(iss[0]["level"], "error")
        self.assertIn("→", iss[0]["msg"])


class TestExplainerProfile(unittest.TestCase):
    def test_profile_and_no_auto_punch_for_code(self):
        sb = {"length_profile": "explainer"}
        prof = duration_profile(sb)
        self.assertEqual(prof["name"], "explainer")
        self.assertGreaterEqual(prof["code_shot_max_sec"], 7.0)
        s = {"id": "C01", "mode": "code", "target_sec": 6.0}
        _, n_default = timeline.punch_plan(s, 6.0, 1.0, 0)
        _, n_explainer = timeline.punch_plan(s, 6.0, 1.0, 0, every=prof["code_change_every_sec"])
        self.assertGreater(n_default, 0)
        self.assertEqual(n_explainer, 0)

    def test_calm_spine_moves(self):
        self.assertTrue(set(spine.CALM) <= set(spine.MOVES))
        self.assertFalse(set(spine.CALM) & spine.ZOOMS)


class TestSceneValidation(unittest.TestCase):
    def test_backdrop_lens_freeze_errors(self):
        errs = html._scene_errors({"actors": [{"id": "r", "icon": "rig:athlete:run", "freeze": 2}], "backdrop": "moon",
                                   "lenses": [{"of": "r.sole", "r": 0.9, "actors": [{"icon": "zzzx"}]}]})
        self.assertEqual(len(errs), 4)
        ok = html._scene_errors({"actors": [{"id": "r", "icon": "rig:athlete:cycle"}], "backdrop": {"kind": "gym", "floor": 0.66},
                                 "lenses": [{"of": "r.knee", "r": 0.3, "actors": [{"icon": "capillary"}], "flow": [{"icon": "rbc"}]}]})
        self.assertEqual(ok, [])
        self.assertIn("road", html.backdrop_kinds())

    def test_detail_icons_known_to_python(self):
        names = html.icon_table()[0]
        for n in ("laptop", "phone", "chip", "macrophage", "chomper", "fat", "glycogen", "spine", "capillary", "bike", "denoise", "receptor"):
            self.assertIn(n, names)
        self.assertEqual(html.icon_for("white blood cell"), "macrophage")
        self.assertEqual(html.icon_for("body fat"), "fat")


@unittest.skipUnless(NODE, "cần node")
class TestVisualsInNode(unittest.TestCase):
    def test_detail_icons_render_finite(self):
        out = _node(
            "import { DETAIL_ICONS } from './engines/html/icons_detail.js';"
            "const bad = [], counts = {};"
            "const fin = (v) => typeof v !== 'number' || Number.isFinite(v);"
            "for (const [n, fn] of Object.entries(DETAIL_ICONS)) for (const p of [0, 0.4, 0.9, 1]) {"
            " const pr = fn({ f: 7, p }); counts[n] = pr.length;"
            " for (const q of pr) { const nums = [q.x, q.y, q.r, q.rx, q.ry, q.w, q.h, ...(q.pts || []).flat()]; if (!nums.every(fin)) bad.push(n); } }"
            "console.log(JSON.stringify({ bad: [...new Set(bad)], counts }));")
        self.assertEqual(out["bad"], [])
        self.assertGreater(out["counts"]["laptop"], 20)
        self.assertGreater(out["counts"]["brain"], 10)

    def test_macrophage_chomps_over_time(self):
        out = _node(
            "import { DETAIL_ICONS } from './engines/html/icons_detail.js';"
            "const m = (f) => DETAIL_ICONS.macrophage({ f, p: 0.6 })[0].pts.length;"
            "const mouth = (f) => { const P = DETAIL_ICONS.macrophage({ f, p: 0.6 })[0].pts; return Math.atan2(P[1][1], P[1][0]); };"
            "console.log(JSON.stringify({ a: mouth(0), b: mouth(4), n: m(0) }));")
        self.assertNotAlmostEqual(out["a"], out["b"], places=3)

    def test_human_rig_actions_and_anchors(self):
        out = _node(
            "import * as R from './engines/html/rig2d.js';"
            "const sp = ['athlete', 'marathoner', 'runnerf', 'lifter', 'casual', 'casualf'], acts = R.ACTIONS, bad = [];"
            "for (const s of sp) for (const a of acts) for (const f of [0, 11]) { const pr = R.rigPrims(`rig:${s}:${a}`, { f }); for (const q of pr) { const v = [q.x, q.y, ...(q.pts || []).flat()]; if (!v.every((x) => x === undefined || Number.isFinite(x))) bad.push(`${s}:${a}`); } }"
            "const an = R.rigAnchors('rig:athlete:run', { f: 5 });"
            "const x0 = R.rigPrims('rig:athlete:run', { f: 5, args: { xray: 1, organs: ['spine', 'muscles', 'fuel', 'brain'], p: 0.5 } }).filter((q) => q.organ).length;"
            "const cyc = R.rigPrims('rig:athlete:cycle', { f: 3 }).length, run = R.rigPrims('rig:athlete:run', { f: 3 }).length;"
            "const fr = R.rigPrims('rig:athlete:run', { f: 30, args: { freeze_f: 10 } }), f10 = R.rigPrims('rig:athlete:run', { f: 10 });"
            "console.log(JSON.stringify({ bad: [...new Set(bad)], keys: Object.keys(an), organs: x0, cyc, run, stride: R.strideOf('rig:athlete:run', 'run'),"
            " frozen: JSON.stringify(fr) === JSON.stringify(f10) }));")
        self.assertEqual(out["bad"], [])
        for k in ("knee", "sole", "spine", "liver", "thigh", "heel", "brain", "hand"):
            self.assertIn(k, out["keys"])
        self.assertGreater(out["organs"], 20)
        self.assertGreater(out["cyc"], out["run"] + 20)       # xe đạp vẽ cùng người
        self.assertGreater(out["stride"], 0.5)
        self.assertTrue(out["frozen"])

    def test_labels_dodge_props_stable_and_fixed(self):
        # vòng 23: nhãn tự do đặt đè lên vật → engine dời ra chỗ trống gần nhất; chỗ chọn giống nhau ở mọi frame;
        # `fixed: true` giữ đúng chỗ người viết đặt.
        out = _node(
            "import { BEATS } from './engines/html/beats.js';"
            "const run = (P, frames) => frames.map((f) => { const drawn = [];"
            " const mk = (f) => ({ g: { save(){}, restore(){}, translate(){}, scale(){}, rotate(){}, beginPath(){}, roundRect(){}, rect(){}, fill(){},"
            "   set filter(v){}, get filter(){ return 'none'; }, set fillStyle(v){}, globalAlpha: 1 },"
            "  W: 1080, H: 1920, N: 60, FPS: 30, f, fs: f, t: f / 30, u: f / 59, A: { top: 300, bottom: 1240, x0: 90, x1: 990, cx: 540 },"
            "  L: { look: 'flat' }, clamp: (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), lerp: (a, b, t) => a + (b - a) * t,"
            "  hash: () => 0.3, strSeed: () => 7, EASE: { smooth: (t) => t }, E: (t) => t, MO: {}, k: () => 1,"
            "  K: { halo(){}, arrow(){}, tag(c, s, x, y){ drawn.push([s, x, y]); }, label(c, s, x, y){ drawn.push([s, x, y]); } },"
            "  enter: (k, b, fn) => fn(), icon(){}, draw(){}, later: (fn) => fn(), text: () => ({ x0: -150, x1: 150, y0: -45, y1: 12 }),"
            "  anchor(){}, iconAnchors: (n, o) => ({ center: [o.x, o.y, o.s * 0.8] }), iconBox: () => [-1, -1, 1, 1],"
            "  pickPart: (an, p) => an[p] || an.center });"
            " const S = BEATS.scene(mk(0), P); S.draw(mk(f)); return drawn[0]; });"
            "const box = { id: 'box', icon: 'server', x: 0.5, y: 0.5, size: 600 };"
            "const a = run({ depth: false, actors: [box], labels: [{ text: 'ON IT', x: 0.5, y: 0.52, u: 0 }] }, [5, 40]);"
            "const b = run({ depth: false, actors: [box], labels: [{ text: 'KEEP', x: 0.5, y: 0.52, u: 0, fixed: true }] }, [5]);"
            "console.log(JSON.stringify({ a, b }));")
        (_, _, y5), (_, _, y40) = out["a"]
        self.assertEqual(y5, y40)                                  # không nhảy giữa các frame
        self.assertTrue(y5 + 22 <= 662 or y5 - 55 >= 1258, y5)     # hộp chữ nằm ngoài vật (vật: y 660..1260)
        self.assertAlmostEqual(out["b"][0][2], 0.52 * 1920, delta=1)

    def test_backdrops_build(self):
        out = _node(
            "import { BACKDROPS, backdropItems } from './engines/html/backdrops.js';"
            "console.log(JSON.stringify(Object.fromEntries(BACKDROPS.map((k) => [k, backdropItems(k, { floor: 0.66 }).length]))));")
        self.assertEqual(set(out), set(html.backdrop_kinds()))
        self.assertTrue(all(v > 10 for v in out.values()))


if __name__ == "__main__":
    unittest.main()
