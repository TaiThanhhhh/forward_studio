"""Kiểm tra vòng nâng cấp chống lặp: layout variants, beat `scene`, spine camera, motiongate, brief & linter."""
import json
import os
import tempfile
import unittest
from unittest import mock

from engines import adapter, html
from vidlib import brief, coderender, codeshot, linter, motiongate, narratives, spine, storyboard
from vidlib.common import ROOT, StudioError, save_json


class TestLayoutsAndScene(unittest.TestCase):
    def test_layouts_validation_and_rotation(self):
        for beat, opts in html.LAYOUTS.items():
            self.assertGreaterEqual(len(opts), 2, beat)
        self.assertEqual(html.validate("title", {"title": "Hi", "layout": "left"}), [])
        self.assertTrue(html.validate("title", {"title": "Hi", "layout": "unknown"}))
        self.assertTrue(html.validate("scale", {"items": [{"label": "a", "size": 1}], "layout": "left"}))

        sb = {
            "slug": "video-a",
            "shots": [
                {"id": "C01", "mode": "code", "code": {"scene": "title", "params": {"title": "One"}}},
                {"id": "C02", "mode": "code", "code": {"scene": "title", "params": {"title": "Two"}}},
                {"id": "C03", "mode": "code", "code": {"scene": "counter", "params": {"to": 10, "layout": "giant"}}},
                {"id": "C04", "mode": "code", "code": {"scene": "counter", "params": {"to": 20}}},
            ],
        }
        codeshot.assign_layouts(sb, "flat-vector-black")
        l1 = sb["shots"][0]["code"]["params"]["layout"]
        l2 = sb["shots"][1]["code"]["params"]["layout"]
        self.assertIn(l1, html.LAYOUTS["title"])
        self.assertIn(l2, html.LAYOUTS["title"])
        self.assertNotEqual(l1, l2)
        self.assertEqual(sb["shots"][2]["code"]["params"]["layout"], "giant")
        self.assertNotEqual(sb["shots"][3]["code"]["params"]["layout"], "giant")

    def test_scene_beat_validates_actors_and_icons(self):
        self.assertTrue(html.validate("scene", {}))
        self.assertTrue(html.validate("scene", {"actors": [{"id": "a", "icon": "nonexistent_xyz"}]}))
        with open(os.path.join(ROOT, "engines", "html", "demo.json"), encoding="utf-8") as fh:
            demo = json.load(fh)
        self.assertEqual(html.validate("scene", demo["scene"]), [])


class TestSpine(unittest.TestCase):
    def test_inverse_roundtrip(self):
        for name, m in spine.MOVES.items():
            inv = spine.inverse(m)
            back = spine.inverse(inv)
            for k in ("x", "y", "s", "r"):
                self.assertAlmostEqual(back[k], m[k], places=6, msg=f"{name}.{k}")

    def test_sequence_avoids_repeats_and_back_to_back_dive_pull(self):
        for style in ("flat-vector-black", "hud-black", "scale-zoom-black", "swiss-motion-black"):
            seq = spine.sequence(12, style, f"seed-{style}")
            self.assertEqual(len(seq), 12)
            for a, b in zip(seq, seq[1:]):
                if len(spine.LOOK_MOVES.get(spine.look_of(style), spine.ALL)) > 1:
                    self.assertNotEqual(a, b, style)
                    self.assertFalse({a, b} <= {"dive", "pull"}, f"{style}: {a}->{b}")

    def test_context_runs_and_L_does_not_leak_across_runs(self):
        segs = [
            {"sid": "C01", "n": 18},   # run 0 ngắn → L=6
            {"sid": "C02", "n": 18},
            {"sid": "C03", "n": 60},   # ngắt chuỗi (non-html)
            {"sid": "C04", "n": 60},   # run 1 dài → L phải theo LOOK_L (không bị kẹp về 6)
            {"sid": "C05", "n": 60},
        ]
        shots = {
            "C01": {"id": "C01", "code": {"scene": "title", "params": {"title": "a"}}},
            "C02": {"id": "C02", "code": {"scene": "fact", "params": {"text": "b"}}},
            "C03": {"id": "C03", "mode": "frames_start"},
            "C04": {"id": "C04", "code": {"scene": "scene", "params": {"actors": []}}},
            "C05": {"id": "C05", "code": {"scene": "outro", "params": {}}},
        }
        ctx = spine.context(
            segs, shots, "flat-vector-black", "slug",
            lambda sh: bool((sh.get("code") or {}).get("scene")),
            lambda sh: {"scene": sh["code"]["scene"], "params": sh["code"].get("params") or {}},
        )
        self.assertEqual(ctx["C01"]["L"], 6)
        self.assertEqual(ctx["C04"]["L"], 9)
        self.assertIn("next", ctx["C01"])
        self.assertIn("prev", ctx["C02"])
        self.assertNotIn("C03", ctx)


class TestNarratives(unittest.TestCase):
    def test_config_is_complete(self):
        self.assertGreaterEqual(len(narratives.ids()), 8)
        for nid in narratives.ids():
            d = narratives.get(nid)
            for k in ("name", "shape", "visual"):
                self.assertTrue(d.get(k), f"{nid}.{k}")
            for m in d.get("moves") or []:
                self.assertIn(m, spine.MOVES, f"{nid}: {m}")
            for p in d.get("strong") or []:
                __import__("re").compile(p)

    def test_title_shape_wins_even_if_recently_used(self):
        cases = {
            "5 things that happen when you stop sleeping": "countdown",
            "What happens to your body after 72 hours without water": "timeline",
            "Is it true that cracking knuckles causes arthritis?": "myth_fact",
            "What if the sun was 10 times bigger": "escalation",
            "Ice vs fire: which melts steel faster": "versus",
        }
        for topic, want in cases.items():
            with mock.patch.object(narratives, "recent", return_value=[want]):
                self.assertEqual(narratives.plan(topic, slug="t")["narrative"], want, topic)

    def test_rotation_skips_recent_and_honours_overrides(self):
        topic = "What happens if you hold a magnet near a phone"
        first = narratives.plan(topic, slug="a")["narrative"]
        with mock.patch.object(narratives, "recent", return_value=[first]):
            self.assertNotEqual(narratives.plan(topic, slug="a")["narrative"], first)
        self.assertEqual(narratives.plan(topic, want="journey")["narrative"], "journey")
        self.assertEqual(narratives.plan(topic, idea={"narrative": "versus"})["narrative"], "versus")
        with self.assertRaises(StudioError):
            narratives.plan(topic, want="nope")

    def test_resolve_keeps_legacy_projects_unchanged(self):
        self.assertEqual(narratives.resolve({}, {}), (None, None))
        self.assertEqual(narratives.resolve({"narrative": "auto"}, {"narrative": "timeline"})[0], "timeline")
        self.assertEqual(narratives.resolve({"narrative": "versus"}, {"narrative": "timeline"})[0], "versus")
        nid, note = narratives.resolve({"narrative": "xyz"}, {})
        self.assertIsNone(nid)
        self.assertTrue(note)

    def test_spine_prefers_narrative_moves_within_look_grammar(self):
        self.assertEqual(set(spine.sequence(6, "swiss-motion-black", "s", narratives.moves("timeline"))), {"pan_r"})
        self.assertEqual(spine.pool_for("swiss-motion-black", narratives.moves("escalation")), ["pan_r", "pan_d"])
        self.assertEqual(spine.look_of("gallery-pointillist-black"), "gallery")      # countdown ∩ gallery = ∅ → theo look
        self.assertEqual(spine.pool_for("gallery-pointillist-black", narratives.moves("countdown")),
                         spine.LOOK_MOVES["gallery"])
        seq = spine.sequence(6, "flat-vector-black", "s", narratives.moves("versus"))
        self.assertTrue(set(seq) <= {"pan_r", "pan_l"})
        self.assertEqual(spine.pool_for("flat-vector-black", None), spine.LOOK_MOVES.get("flat", spine.ALL))


class TestSpineManimTravel(unittest.TestCase):
    def test_travel_matrix_only_inside_windows_and_meets_html_camera_at_cut(self):
        sp = {"L": 8, "next": {"n": 60, "tile": dict(spine.MOVES["pan_r"])},
              "prev": {"n": 60, "tile": spine.inverse(spine.MOVES["dive"])}}
        n = 60
        self.assertIsNone(spine.travel_matrix(sp, 30, n, 1080, 1920))
        self.assertIsNone(spine.travel_matrix(None, 0, n, 1080, 1920))
        m = spine.travel_matrix(sp, n - 1, n, 1080, 1920)        # cuối shot: camera lia sang phải → hình trôi sang trái
        self.assertLess(m[0][2], -50)
        m0 = spine.travel_matrix(sp, 0, n, 1080, 1920)           # đầu shot sau một cú "dive": ô này còn nhỏ, đang lớn dần
        self.assertLess(m0[0][0], 1.0)
        m7 = spine.travel_matrix(sp, 7, n, 1080, 1920)
        self.assertGreater(m7[0][0], m0[0][0])

    def test_manim_shots_join_the_one_take_as_ghost_tiles(self):
        sb = {"slug": "m", "shots": [
            {"id": "C01", "mode": "code", "code": {"scene": "graph", "params": {"points": [[0, 1], [1, 2]]}}},
            {"id": "C02", "mode": "code", "code": {"scene": "scale", "params": {"items": [{"label": "a", "size": 1}]}}},
        ]}
        tl = {"segments": [{"sid": "C01", "n": 60}, {"sid": "C02", "n": 60}]}
        ctx = codeshot.spine_context(sb, tl, "physics-diagram-black")
        self.assertEqual(codeshot.engine_of(sb["shots"][0], "physics-diagram-black"), "manim")
        self.assertEqual(codeshot.engine_of(sb["shots"][1], "physics-diagram-black"), "html")
        self.assertTrue(ctx["C02"]["prev"]["ghost"])               # html không vẽ lại sơ đồ Manim
        self.assertIn("next", ctx["C01"])
        with tempfile.TemporaryDirectory() as proj:
            jp = codeshot.job_for(proj, sb, sb["shots"][0], 60, "physics-diagram-black", ctx["C01"])
            j = adapter.load_job(jp)
            self.assertEqual(set(j["spine"]["next"]), {"n", "tile"})  # nội dung hàng xóm không vào hash job Manim
            self.assertTrue(j["qa_frames"])


class TestHaveAllHashAndMotionGate(unittest.TestCase):
    def test_have_all_checks_job_hash(self):
        with tempfile.TemporaryDirectory() as proj:
            sid = "C01"
            spec = adapter.ShotSpec(
                sid=sid, engine="html", scene="title", params={"title": "A"},
                frames=2, style="hud-black", work=codeshot.code_dir(proj, sid),
            )
            jp = adapter.get("html").job(spec)
            fdir = codeshot.frames_dir(proj, sid)
            os.makedirs(fdir, exist_ok=True)
            for f in range(2):
                with open(os.path.join(fdir, f"f{f:04d}.jpg"), "wb") as fh:
                    fh.write(b"x")
            self.assertFalse(codeshot.have_all(proj, sid, 2))  # thiếu _job.hash
            with open(jp, encoding="utf-8") as fh:
                job_data = json.load(fh)
            h = coderender.job_hash(job_data)
            with open(os.path.join(fdir, "_job.hash"), "w", encoding="utf-8") as fh:
                fh.write(h)
            self.assertTrue(codeshot.have_all(proj, sid, 2))
            save_json(jp, {**job_data, "params": {"title": "B"}})
            self.assertFalse(codeshot.have_all(proj, sid, 2))  # job đổi → cache cũ vô hiệu

    def test_motiongate_verdict(self):
        self.assertFalse(motiongate.verdict({"rapid": 0.02})[1])
        lbl, ok = motiongate.verdict({"rapid": 0.05})
        self.assertTrue(ok)
        self.assertIn("tĩnh", lbl)
        self.assertTrue(motiongate.verdict({"rapid": 0.12})[1])


class TestBriefAndLinterVariety(unittest.TestCase):
    def test_brief_teaches_scene_layouts_and_narrative_variety(self):
        h = brief.engine_help()
        self.assertIn("`scene`", h)
        self.assertIn("LAYOUT", h.upper())
        p = brief.plan_block({"style": "flat-vector-black", "uses_flow": False, "reason": "r"})
        self.assertIn("scene", p)
        with open(os.path.join(ROOT, "prompts", "storyboard_brief.md"), encoding="utf-8") as fh:
            md = fh.read()
        self.assertIn("{narrative_block}", md)
        self.assertIn("never force every video into the same template", narratives.block(None))
        b = brief.build("5 things that happen when you stop sleeping", "x",
                        plan={"style": "flat-vector-black", "uses_flow": False, "reason": "r", "narrative": "countdown"})
        self.assertIn("NARRATIVE SHAPE FOR THIS VIDEO:** `countdown`", b)
        self.assertNotIn("{narrative_block}", b)

    def test_linter_warns_when_all_html_shots_are_template_only(self):
        shots = [
            {"id": f"C0{i}", "beat": "hook" if i == 1 else ("payoff" if i == 5 else "escalate"),
             "mode": "code", "target_sec": 2.0, "vo": "Two words here.",
             "code": {"scene": sc, "params": par}}
            for i, (sc, par) in enumerate([
                ("title", {"title": "A"}),
                ("counter", {"to": 10}),
                ("process", {"steps": [{"label": "x"}]}),
                ("callout", {"icon": "ball", "labels": [{"text": "y"}]}),
                ("compare", {"left": {"label": "a", "value": 1}, "right": {"label": "b", "value": 2}}),
            ], 1)
        ]
        sb = storyboard.normalize({"topic": "t", "style": "flat-vector-black", "language": "en", "shots": shots})
        sb["style_resolved"] = "flat-vector-black"
        for s in sb["shots"]:
            s["mode_resolved"] = "code"
        warns = [i["msg"] for i in linter.lint_pacing(sb) if i["level"] == "warn"]
        self.assertTrue(any("scene" in w for w in warns), warns)
        sb["shots"][2]["code"] = {"scene": "scene", "params": {"actors": [{"id": "a", "icon": "ball"}]}}
        warns2 = [i["msg"] for i in linter.lint_pacing(sb) if i["level"] == "warn"]
        self.assertFalse(any("scene" in w for w in warns2), warns2)


class TestThree3DAndFlow3D(unittest.TestCase):
    @unittest.skipUnless(__import__("shutil").which("node"), "cần node")
    def test_stage_supports_all_universe_3d_props_mannequin_parts_and_fx(self):
        import subprocess

        code = """
        import * as THREE from './vendor/three/three.module.js';
        import * as MO from './lib/motion/motion.js';
        import * as PROPS from './engines/three/props.js';
        import * as CAST from './engines/three/cast.js';
        import { build } from './engines/three/scenes/stage.js';
        const world = new THREE.Group();
        const ctx = {
          THREE, MO, PROPS, CAST, world, N: 30, fps: 30, job: { font_family: 'sans-serif' },
          C: (k) => '#ffffff',
          toon: () => new THREE.MeshBasicMaterial(),
          flat: () => new THREE.MeshBasicMaterial(),
          glow: () => new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial()),
          add: (geo, m, x=0, y=0, z=0, p=world) => {
            const me = new THREE.Mesh(geo, typeof m === 'string' ? new THREE.MeshBasicMaterial() : m);
            me.position.set(x, y, z); p.add(me); return me;
          },
          group: (p=world, x=0, y=0, z=0) => { const g = new THREE.Group(); g.position.set(x, y, z); p.add(g); return g; },
        };
        const types = [
          'mannequin', 'runner3d', 'lifter3d',
          'shoe', 'bottle', 'stopwatch', 'heart', 'lungs', 'brain', 'cell', 'medal', 'trophy', 'track',
          'dumbbell', 'barbell', 'kettlebell', 'weightplate', 'shaker', 'muscle',
          'camera', 'clapper', 'waveform',
          'laptop', 'server', 'bug', 'database', 'phone', 'battery', 'chip', 'lock', 'key',
          'beaker', 'flask', 'burner', 'syringe', 'anvil', 'pendulum', 'flame', 'drop', 'magnet', 'rocket', 'planet',
          'clock', 'hourglass',
          'dna', 'virus', 'mitochondria', 'volcano',
        ];
        const props = types.map((t, i) => ({
          id: 'p' + i, type: t, at: [(i % 5) * 0.4, Math.floor(i / 5) * 0.4, 0],
          keys: [{ u: 0.5, value: 0.8 }],
        }));
        props.push({ type: 'parts', parts: [{ k: 'box', size: [0.2, 0.2, 0.2] }, { k: 'sphere', r: 0.12 }] });
        const s = build(ctx, {
          set: 'track',
          props,
          fx: [
            { kind: 'steam', of: 'p0', u: [0, 1] },
            { kind: 'sparks', at: [0, 0.5, 0], u: [0, 1] },
            { kind: 'shockwave', at: [0, 0, 0], u: [0.2, 0.8] },
          ],
        });
        const f0 = s.frame(0), f15 = s.frame(15), f29 = s.frame(29);
        console.log(JSON.stringify({ ok: Boolean(f0.cam && f15.cam && f29.cam), n: types.length }));
        """
        r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True, check=True)
        out = json.loads(r.stdout.strip())
        self.assertTrue(out["ok"])
        self.assertGreaterEqual(out["n"], 45)

    def test_brief_three_help_lists_3d_actors_props_and_fx(self):
        h = brief._three_help()
        for kw in ("mannequin", "shoe", "dumbbell", "laptop", "flask", "fx[]:", "icon3d"):
            self.assertIn(kw, h, kw)

    def test_clay3d_black_and_3d_flow_compiler(self):
        from tests.helpers import mini
        from vidlib import compiler, styles

        self.assertIn("clay3d-black", styles.available())
        self.assertTrue(styles.uses_flow("clay3d-black"))
        sb = mini(style="clay3d-black")
        sb["style_resolved"] = "clay3d-black"
        compiled = compiler.compile_all(sb)
        shot = compiled["shots"][0]
        self.assertIn("Stylized 3D clay diorama", shot["start_frame"]["prompt"])
        self.assertNotIn("3D render", shot["start_frame"]["prompt"])
        self.assertIn("Stylized 3D clay diorama", shot["video_prompt"])
        self.assertNotIn("3D shading", shot["video_prompt"])
        self.assertIn("Background stays pure black and static", shot["video_prompt"])
        self.assertNotIn("3D render", compiled["outro"]["bg_prompt"])
        self.assertNotIn("3D shading", compiled["outro"]["bg_prompt"])
        self.assertIn("Stylized 3D clay diorama", compiler.style_bible(compiled))
        errs = [i for i in linter.lint(compiled) if i["level"] == "error"]
        self.assertEqual(errs, [])

    def test_hybrid_multi_engine_mixing_shares_style_palette(self):
        with tempfile.TemporaryDirectory() as proj:
            sb = storyboard.normalize({
                "topic": "Hybrid 3D + Charts + Manim",
                "style": "hud-black",
                "language": "en",
                "shots": [
                    {"id": "C01", "beat": "hook", "mode": "code", "target_sec": 2.0,
                     "code": {"scene": "stage", "params": {"props": [{"type": "mannequin", "pose": "run"}]}}},
                    {"id": "C02", "beat": "setup", "mode": "code", "target_sec": 2.0,
                     "code": {"scene": "graph", "params": {"title": "Heart Rate", "points": [[0, 60], [1, 180]]}}},
                    {"id": "C03", "beat": "escalate", "mode": "code", "target_sec": 2.0,
                     "code": {"engine": "manim", "scene": "equation", "params": {"lines": [{"text": "F = m * a"}]}}},
                    {"id": "C04", "beat": "payoff", "mode": "code", "target_sec": 2.0,
                     "code": {"scene": "counter", "params": {"to": 200, "unit": "BPM"}}},
                ],
            })
            errs, _ = storyboard.validate(sb)
            self.assertEqual(errs, [])
            self.assertEqual(codeshot.engine_of(sb["shots"][0], "hud-black"), "three")
            self.assertEqual(codeshot.engine_of(sb["shots"][1], "hud-black"), "html")
            self.assertEqual(codeshot.engine_of(sb["shots"][2], "hud-black"), "manim")
            self.assertEqual(codeshot.engine_of(sb["shots"][3], "hud-black"), "html")

            j3 = adapter.load_job(codeshot.job_for(proj, sb, sb["shots"][0], 30, "hud-black"))
            jh = adapter.load_job(codeshot.job_for(proj, sb, sb["shots"][1], 30, "hud-black"))
            # Cả shot 3D (`three`) lẫn shot biểu đồ (`html`) trong cùng video `hud-black` đều dùng chung màu accent #3CE6C8
            self.assertEqual(j3["world"]["colors"]["accent"].upper(), jh["look"]["palette"]["a"].upper())


if __name__ == "__main__":
    unittest.main()
