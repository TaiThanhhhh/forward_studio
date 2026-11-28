"""Vòng 10 WP-M — bộ não motion: động từ chuyển động (JS = Python), kho cơ chế, chữ ký motion, chống lặp giữa video."""
import copy
import json
import os
import shutil
import subprocess
import unittest
from unittest import mock

import lib.motion as mo
from vidlib import brief, codeshot, motionplan, spine
from vidlib.common import ROOT, channel

TS = [-0.3, 0, 0.013, 0.05, 0.1, 0.17, 0.25, 0.33, 0.41, 0.5, 0.62, 0.77, 0.9, 1.0, 1.3, 2.71, 7.9]
ARGS = [{}, {"seed": "dog-7", "bpm": 157, "dir": "up", "from": "right", "axis": "x", "count": 3, "dur": 1.2}]
PLAY = [{"u": 0.1, "verb": "drop-bounce"}, {"t": 0.4, "verb": "heartbeat", "args": {"bpm": 140}},
        {"f": 30, "verb": "fly_off", "dur": 0.3}, {"u": 0, "verb": "pop", "stagger": "center_out", "args": {"each": 0.1}}]
JS = """
import * as m from './lib/motion/motion.js';
const TS = %s, ARGS = %s, PLAY = %s;
const out = {verbs: {}};
for (const n of Object.keys(m.VERBS)) out.verbs[n] = ARGS.map(a => TS.map(t => m.verb(n, t, a)));
out.meta = m.VERBS; out.alias = m.VERB_ALIASES; out.staggers = m.STAGGERS;
out.stag = m.STAGGERS.map(p => [0, 1, 2, 5, 8].map(i => m.stagger(p, i, 9, {seed: 'x', cols: 3})));
out.play = [0, 7, 15, 31, 59].map(f => m.play(PLAY, f, 60, 30, 2, 5));
out.hash = [[0, 0], [1, 2], [4294967295, -7], [123456, 3.7]].map(([a, b]) => m.hash01(a, b));
out.seed = ['', 'dog', 'Đà Lạt', 42, -3, 2.9].map(s => m.seedOf(s));
out.sec = m.verb('heartbeat', 0.5, {bpm: 120, sec: 0.27});
console.log(JSON.stringify(out));
"""

STYLE = "flat-vector-black"


def html_sb(slug, topic="What happens to your heart when you play GTA 6 all night?"):
    shots = [
        ("title", {"title": "All night"}), ("counter", {"to": 157, "unit": "BPM", "label": "Heart rate at 157 bpm"}),
        ("compare", {"left": {"label": "A", "value": 72}, "right": {"label": "B", "value": 157}}),
        ("scene", {"actors": [{"id": "h", "icon": "heart"}]}), ("counter", {"to": 188}),
        ("compare", {"left": {"label": "A", "value": 1}, "right": {"label": "B", "value": 3}}),
        ("process", {"steps": [{"label": "a"}, {"label": "b"}, {"label": "c"}]}), ("fact", {"text": "Twist"}),
    ]
    return {"slug": slug, "topic": topic, "style": STYLE, "style_resolved": STYLE,
            "shots": [{"id": f"C{i:02d}", "beat": "escalate", "mode": "code", "mode_resolved": "code", "vo": "Words.",
                       "code": {"scene": sc, "params": dict(p)}} for i, (sc, p) in enumerate(shots, 1)]}


class TestVerbs(unittest.TestCase):
    def test_vocabulary_groups_docs(self):
        self.assertGreaterEqual(len(mo.VERBS), 30)
        groups = {v["g"] for v in mo.VERBS.values()}
        self.assertEqual(groups, {"in", "accent", "out", "idle"})
        for g in groups:
            self.assertGreaterEqual(sum(v["g"] == g for v in mo.VERBS.values()), 8, g)
        self.assertEqual(set(mo.VERBS), set(mo.VERB_DOC))                    # mọi verb có mô tả cho brief
        for want in ("pop", "drop_bounce", "slide_overshoot", "unfold", "draw_on", "iris", "typewriter", "assemble",
                     "grow_from", "shatter_in", "pulse", "shake", "squash", "wobble", "jiggle", "heartbeat", "flip",
                     "flash", "ripple", "fly_off", "fall_away", "dissolve", "fold", "breathe", "float", "sway",
                     "follow_through"):
            self.assertIn(want, mo.VERBS)
        self.assertEqual(set(mo.STAGGERS), {"cascade", "reverse", "center_out", "edges_in", "wave", "random", "diagonal"})
        self.assertEqual(mo.verb_name("Drop-Bounce"), "drop_bounce")
        self.assertEqual(mo.verb_name("fade_out"), "dissolve")
        self.assertIsNone(mo.verb_name("teleport"))
        self.assertEqual(mo.verb("teleport", 0.3), mo.identity())          # tên lạ: không làm gì, không lỗi khi render

    def test_shapes_in_out_accent(self):
        ident = mo.identity()
        for n, meta in mo.VERBS.items():
            d0, d_end = mo.verb(n, -0.1), mo.verb(n, 50.0, {"dur": 0.5} if meta["dur"] is None else {})
            if meta["g"] == "in":
                self.assertLess(min(d0["alpha"], d0["reveal"], d0["sx"] if n != "drop_bounce" else 0), 0.05, n)
                for k, v in d_end.items():
                    self.assertAlmostEqual(v, ident[k], places=6, msg=f"{n}.{k} cuối phải về nguyên dạng")
            elif meta["g"] == "out":
                self.assertEqual(d0, ident, n)
                self.assertAlmostEqual(d_end["alpha"], 0.0, places=6, msg=n)
            else:
                self.assertEqual(d0, ident, n)
                if n not in ("swell", "shrink", "spin"):
                    for k, v in d_end.items():
                        self.assertAlmostEqual(v, ident[k], places=4, msg=f"{n}.{k}")
        self.assertAlmostEqual(mo.verb("swell", 9, {"amp": 0.3})["sx"], 1.3)  # swell giữ trạng thái mới
        self.assertGreater(max(mo.verb("pop", t / 100)["sx"] for t in range(36)), 1.0)    # pop vượt quá

    def test_heartbeat_follows_real_bpm(self):
        for bpm in (72, 157):
            beats, prev = 0, 1.0
            for f in range(60 * 120):                                      # 60 s ở 120 Hz, đếm đủ cả hai đỉnh lub + dub
                s = mo.verb("heartbeat", f / 120, {"bpm": bpm})["sx"]
                if prev <= 1.0 + 1e-9 < s:
                    beats += 1
                prev = s if s > 1.0 + 1e-9 else 1.0
            self.assertLessEqual(abs(beats - 2 * bpm), 3, f"{bpm} bpm → {beats} cú (lub + dub)")
        self.assertAlmostEqual(mo.verb("heartbeat", 0.9, {"bpm": 120, "sec": 0.27})["sx"],
                               mo.verb("heartbeat", 0.27, {"bpm": 120})["sx"])   # shim (tiến độ, {sec}) của beats.js

    def test_play_stagger_compose(self):
        a = mo.play([{"u": 0.5, "verb": "pop"}], 0, 61)
        self.assertEqual(a["alpha"], 0.0)                                   # chưa tới lúc vào → ẩn
        b = mo.play([{"u": 0.5, "verb": "pop"}], 60, 61)
        self.assertAlmostEqual(b["sx"], 1.0)
        c = mo.compose({"x": 1, "sx": 2}, {"x": 0.5, "sx": 0.5})
        self.assertEqual((c["x"], c["sx"]), (1.5, 1.0))
        self.assertEqual([mo.stagger("center_out", i, 5) for i in (0, 2, 4)], [0.16, 0.0, 0.16])
        self.assertEqual(mo.stagger("random", 3, 9, {"seed": "s"}), mo.stagger("random", 3, 9, {"seed": "s"}))
        errs = mo.verb_errors([{"verb": "drop_bounse"}, {"verb": "pop", "args": {"zz": 1}}, {"verb": "pop",
                                                                                         "stagger": "spiral"}])
        self.assertEqual(len(errs), 3)
        self.assertIn("drop_bounce", errs[0])                               # gợi ý tên gần

    @unittest.skipUnless(shutil.which("node"), "cần node để chạy bản JS")
    def test_js_parity_every_verb(self):
        code = JS % (json.dumps(TS), json.dumps(ARGS), json.dumps(PLAY))
        r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        js = json.loads(r.stdout)
        meta = {k: {"g": v["g"], "dur": v["dur"], "args": v["args"]} for k, v in mo.VERBS.items()}
        self.assertEqual(meta, js["meta"])
        self.assertEqual(mo.VERB_ALIASES, js["alias"])
        self.assertEqual(list(mo.STAGGERS), js["staggers"])
        for n in mo.VERBS:
            for ai, a in enumerate(ARGS):
                for ti, t in enumerate(TS):
                    py, j = mo.verb(n, t, a), js["verbs"][n][ai][ti]
                    for k, v in py.items():
                        self.assertAlmostEqual(float(v), float(j[k]), places=9, msg=f"{n} t={t} args={a} {k}")
        for p, row in zip(mo.STAGGERS, js["stag"]):
            for i, v in zip((0, 1, 2, 5, 8), row):
                self.assertAlmostEqual(mo.stagger(p, i, 9, {"seed": "x", "cols": 3}), v, places=12, msg=p)
        for f, j in zip((0, 7, 15, 31, 59), js["play"]):
            py = mo.play(PLAY, f, 60, 30, 2, 5)
            for k in py:
                self.assertAlmostEqual(py[k], j[k], places=9, msg=f"play f={f} {k}")
        self.assertEqual([mo.hash01(a, b) for a, b in [[0, 0], [1, 2], [4294967295, -7], [123456, 3.7]]], js["hash"])
        self.assertEqual([mo.seed_of(s) for s in ["", "dog", "Đà Lạt", 42, -3, 2.9]], js["seed"])
        for k, v in mo.verb("heartbeat", 0.5, {"bpm": 120, "sec": 0.27}).items():
            self.assertAlmostEqual(v, js["sec"][k], places=9)


class TestMetaphors(unittest.TestCase):
    def test_library_size_and_validity(self):
        ms = motionplan.metaphors()
        self.assertGreaterEqual(len(ms), 150)
        self.assertEqual(len({m["id"] for m in ms}), len(ms))
        self.assertEqual(motionplan.check_library(), [])                   # mọi tên trong recipe có thật (đọc động)
        areas = {m.get("area") for m in ms}
        for want in ("body", "fitness", "tech", "ai", "lab", "animals", "space", "money", "sleep", "food", "nature"):
            self.assertIn(want, areas)
        self.assertGreaterEqual(sum(bool(m.get("general")) for m in ms), 8)
        for m in ms:
            self.assertIsNotNone(motionplan.usable_recipe(m), m["id"])     # luôn có recipe chạy được ngay
            self.assertTrue(set(m["depth"]) <= {"far", "mid", "near"}, m["id"])
            for kw in m["keywords"]:
                self.assertEqual(kw, kw.lower(), m["id"])

    def test_validator_catches_invented_names_and_feature_detects(self):
        err, need = motionplan.recipe_errors({"engine": "html", "scene": "scene", "params": {
            "actors": [{"id": "a", "icon": "unicorn_xyz", "keys": [{"u": 0.2, "verb": "teleport"}]}], "wibble": 1}})
        self.assertTrue(any("unicorn_xyz" in e for e in err))
        self.assertTrue(any("teleport" in e for e in err))
        self.assertTrue(any("wibble" in e for e in err))
        err, need = motionplan.recipe_errors({"engine": "html", "scene": "hologram_beat", "params": {}})
        self.assertEqual(err, [])
        self.assertEqual(need, {"beat:hologram_beat"})                      # beat chưa có → cần, không phải lỗi
        e = motionplan.entry_errors({"id": "x", "keywords": ["x"], "mechanism": "m", "verbs": ["pop"], "avoid": "a",
                                     "depth": {"mid": "m"}, "recipe": {"engine": "html", "scene": "hologram_beat",
                                                                       "params": {}}})
        self.assertTrue(any("requires" in x for x in e))
        e2 = motionplan.entry_errors({"id": "x", "keywords": ["x"], "mechanism": "m", "verbs": ["pop"], "avoid": "a",
                                      "depth": {"mid": "m"},
                                      "recipe": {"engine": "html", "scene": "hologram_beat", "params": {},
                                                 "requires": ["beat:hologram_beat"]},
                                      "fallback": {"engine": "html", "scene": "fact", "params": {"text": "t"}}})
        self.assertEqual(e2, [])
        err, _ = motionplan.recipe_errors({"engine": "html", "scene": "meter", "params": {"kind": "lava_lamp"}})
        self.assertTrue(any("lava_lamp" in x for x in err))                 # enum đọc từ PARAMS

    def test_matching_uses_word_stems(self):
        ids = [r[0] for r in motionplan.match("Why does sleeping badly after an all-nighter wreck you?")]
        self.assertIn("sleep_debt_tank", ids)
        ids = [r[0] for r in motionplan.match("What a marathon runner's heart rate does at 157 bpm")]
        self.assertIn("heart_rate_ecg", ids[:3])


class TestSignatureAndLint(unittest.TestCase):
    def test_signature_metrics(self):
        sb = html_sb("x-sig")
        sig = motionplan.signature(sb, STYLE)
        self.assertEqual(sig["skeleton"][:3], ["title", "counter", "compare"])
        self.assertAlmostEqual(sig["metrics"]["generic_share"], 6 / 8)
        self.assertEqual(sig["metrics"]["mechanism_shots"], 2)              # scene + process
        self.assertEqual(motionplan.skeleton_sim(["a", "b"], ["a", "b"]), 1.0)
        self.assertEqual(motionplan.skeleton_sim(["a", "b", "c"], ["c", "b", "a"]),
                         motionplan.skeleton_sim(["c", "b", "a"], ["a", "b", "c"]))   # đối xứng
        self.assertLess(motionplan.skeleton_sim(["title", "counter"], ["stage", "split"]), 0.01)

    def test_lint_warns_with_alternatives_and_can_block(self):
        sb = html_sb("x-lint")
        prev = motionplan.signature(html_sb("x-prev"), STYLE)
        prev["slug"] = "x-prev"
        with mock.patch.object(motionplan, "recent", return_value=[prev]):
            from vidlib import linter
            issues = linter.lint_motion(sb)
            warns = [i["msg"] for i in issues if i["level"] == "warn"]
            self.assertTrue(any("chung chung" in w and "Gợi ý" in w for w in warns), warns)
            self.assertTrue(any("CƠ CHẾ" in w for w in warns), warns)
            self.assertTrue(any("Khung xương giống" in w for w in warns), warns)
            self.assertTrue(any(i["level"] == "info" and i["where"].startswith("C") for i in issues))
            with mock.patch.object(motionplan, "cfg", return_value={**motionplan.cfg(), "block": True}):
                self.assertTrue(any(i["level"] == "error" for i in linter.lint_motion(sb)))
        bad = html_sb("x-bad")
        bad["shots"][3]["mechanism"] = "hart_rate_ecg"
        bad["shots"][3]["code"]["params"]["actors"][0]["keys"] = [{"u": 0.3, "verb": "drop_bounse"}]
        with mock.patch.object(motionplan, "recent", return_value=[]):
            msgs = " ".join(i["msg"] for i in motionplan.lint(bad, lambda lv, w, m: {"level": lv, "where": w, "msg": m}))
        self.assertIn("heart_rate_ecg", msgs)
        self.assertIn("drop_bounce", msgs)


class TestAntiRepeat(unittest.TestCase):
    def test_same_topic_twice_changes_layouts_moves_mechanisms(self):
        topic = "What happens to your heart when you play GTA 6 all night?"
        with mock.patch.object(motionplan, "recent", return_value=[]):
            a = html_sb("same-topic-a", topic)
            codeshot.assign_layouts(a, STYLE)
            moves_a = spine.sequence(7, STYLE, "same-topic-a", avoid=motionplan.recent_moves("same-topic-a"))
            mech_a = [m["id"] for m in motionplan.for_topic(topic, "same-topic-a")]
        sig = motionplan.signature(a, STYLE, slug="same-topic-a")
        sig["moves"] = moves_a
        sig["mechanisms"] = mech_a[:3]
        with mock.patch.object(motionplan, "recent", return_value=[sig]):
            b = html_sb("same-topic-b", topic)
            codeshot.assign_layouts(b, STYLE)
            moves_b = spine.sequence(7, STYLE, "same-topic-b", avoid=motionplan.recent_moves("same-topic-b"))
            mech_b = [m["id"] for m in motionplan.for_topic(topic, "same-topic-b")]
            brief_b = motionplan.brief_block(topic, "same-topic-b")
        la = [(s["code"]["scene"], s["code"]["params"].get("layout")) for s in a["shots"]]
        lb = [(s["code"]["scene"], s["code"]["params"].get("layout")) for s in b["shots"]]
        same = [x for x, y in zip(la, lb) if x == y and x[1]]
        self.assertEqual(same, [], f"bố cục lặp: {same}")
        self.assertFalse(set(moves_a) & set(moves_b), (moves_a, moves_b))
        self.assertFalse(set(mech_a[:3]) & set(mech_b), (mech_a, mech_b))
        self.assertIn("DO NOT REPEAT", brief_b)
        self.assertIn("same-topic-a", brief_b)
        per_beat = {}
        for sc, lay in lb:
            if lay:
                per_beat.setdefault(sc, []).append(lay)
        for sc, lays in per_beat.items():
            self.assertEqual(len(lays), len(set(lays)), sc)

    def test_spine_new_moves(self):
        new = set(spine.ALL) - set(spine.LEGACY_ALL)
        self.assertGreaterEqual(len(new), 4)
        for m in new:
            inv = spine.inverse(spine.MOVES[m])
            back = spine.inverse(inv)
            for k in ("x", "y", "s", "r"):
                self.assertAlmostEqual(back[k], spine.MOVES[m][k], places=6)
            sp = {"L": 8, "next": {"n": 60, "tile": spine._tile(m)}}
            self.assertIsNotNone(spine.travel_matrix(sp, 59, 60, 1080, 1920))
        seq = spine.sequence(30, STYLE, "zz")
        for x, y in zip(seq, seq[1:]):
            self.assertFalse(x in spine.ZOOMS and y in spine.ZOOMS, (x, y))
        self.assertEqual(spine._tile("rack")["fx"], "rack")
        self.assertNotIn("fx", spine._tile("pan_r"))

    def test_brief_differs_by_topic(self):
        with mock.patch.object(motionplan, "recent", return_value=[]):
            b1 = motionplan.brief_block("What happens to a dog's nose when it sniffs a flower?", "t-dog")
            b2 = motionplan.brief_block("What happens to your phone battery in freezing cold?", "t-battery")
        i1 = {ln.split("`")[1] for ln in b1.splitlines() if ln.strip()[:2].rstrip(".").isdigit() and "`" in ln}
        i2 = {ln.split("`")[1] for ln in b2.splitlines() if ln.strip()[:2].rstrip(".").isdigit() and "`" in ln}
        self.assertIn("dog_sniff", i1)
        self.assertIn("battery_drain", i2)
        self.assertLessEqual(len(i1 & i2), 3)                               # chỉ cơ chế tổng quát có thể trùng
        for b in (b1, b2):
            self.assertIn("MECHANISM IDEAS FOR THIS TOPIC", b)
            self.assertIn("MOTION VERBS", b)
            self.assertIn("`heartbeat`", b)                                 # từ vựng verb đọc từ lib/motion

    def test_full_brief_has_motion_block_and_mechanism_first_mix(self):
        with mock.patch.object(motionplan, "recent", return_value=[]):
            t = brief.build("What happens to a dog's nose when it sniffs a flower?", "t-dog2")
        self.assertIn("## 4c. Motion", t)
        self.assertNotIn("{motion_block}", t)
        self.assertIn('"engine": "three"', t)                               # JSON recipe không bị gộp ngoặc hỏng
        mix = brief.mix_help()
        self.assertIn("mechanism first", mix)
        self.assertLess(mix.index("physically happens"), mix.index("A number ALONE"))

    def test_config_block(self):
        m = channel()["motion"]
        for k in ("avoid_recent", "generic_max_share", "min_mechanism_shots", "skeleton_sim_max", "metaphors_top_k"):
            self.assertIn(k, m)


@unittest.skipUnless(motionplan.projects(), "cần dự án thật trong projects/")
class TestRealProjects(unittest.TestCase):
    def test_audit_finds_the_template(self):
        rows = motionplan.audit()
        self.assertGreaterEqual(len(rows), 3)
        legacy_rows = [(s, sig, m) for s, sig, m in rows if motionplan.legacy(s)]
        if not legacy_rows:                    # vòng 23: chủ kênh đã xoá video cũ (khuôn mẫu) để giảm dung lượng
            self.skipTest("không còn dự án cũ (trước vòng 10) trong projects/ để đối chiếu")
        self.assertTrue(all(m["verbs_distinct"] == 0 for _, _, m in legacy_rows))  # trước vòng 10: không có verb nào
        heavy = [s for s, _, m in rows if m["generic_share"] > float(motionplan.cfg()["generic_max_share"])]
        self.assertGreaterEqual(len(heavy), 2, heavy)
        for _, sig, _ in legacy_rows:                                      # video cũ chỉ một kiểu vào (theo look)
            self.assertLessEqual(len(sig["entrances"]), 1)

    def test_legacy_projects_rebuild_identically(self):
        for slug in motionplan.projects():
            if not motionplan.legacy(slug):
                continue
            d = os.path.join(ROOT, "projects", slug)
            with open(os.path.join(d, "storyboard.json"), encoding="utf-8") as fh:
                sb = json.load(fh)
            jobs = {}
            code = os.path.join(d, "work", "code")
            for sid in os.listdir(code) if os.path.isdir(code) else []:
                jp = os.path.join(code, sid, "job.json")
                if os.path.exists(jp):
                    with open(jp, encoding="utf-8") as fh:
                        jobs[sid] = json.load(fh)
            tp = os.path.join(d, "work", "timeline.json")
            if not jobs or not os.path.exists(tp):
                continue
            c = copy.deepcopy(sb)
            c["slug"] = slug
            style = sb.get("style_resolved") or sb.get("style")
            o = jobs.get("OUTRO")
            oshot = {"id": "OUTRO", "beat": "outro", "code": {"scene": o["scene"], "params": dict(o["params"])}} if o \
                else None
            codeshot.assign_layouts(c, style, [oshot] if oshot else None)
            for s in c["shots"]:
                j = jobs.get(s["id"])
                if j and j.get("engine") == "html":
                    self.assertEqual(s["code"]["params"].get("layout"), j["params"].get("layout"), f"{slug}/{s['id']}")
            with open(tp, encoding="utf-8") as fh:
                tl = json.load(fh)
            ctx = codeshot.spine_context(c, tl, style, {"OUTRO": oshot} if oshot else None)
            for sid, j in jobs.items():
                for k in ("move_in", "move_out"):
                    self.assertEqual((j.get("spine") or {}).get(k), (ctx.get(sid) or {}).get(k), f"{slug}/{sid}.{k}")


if __name__ == "__main__":
    unittest.main()
