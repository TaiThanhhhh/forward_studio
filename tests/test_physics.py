"""Vật lý vật rắn của cảnh `stage` (engines/three/physics.js + Rapier tất định trong vendor/rapier/): rơi đúng thời gian
rơi tự do, chạy lại giống hệt, hit_u canh va chạm đúng frame (kể cả có slow-mo), chồng hộp đứng yên, lông vũ rơi chậm,
thả sau keyframe giữ đà, vật kinematic đẩy vật động, va chạm sinh cue/kick, kiểm dữ liệu storyboard."""
import hashlib
import json
import math
import os
import shutil
import subprocess
import unittest

from engines import adapter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join("tests", "fixtures", "stage_harness.mjs")


def stage(params, frames=60):
    r = subprocess.run(["node", HARNESS, json.dumps({"frames": frames, "params": params})], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", check=True, timeout=120)
    return json.loads(r.stdout.strip())


def first_impact(out, pid):
    return next((h["f"] for h in out["physics"]["impacts"] if h["id"] == pid), None)


@unittest.skipUnless(shutil.which("node"), "cần node")
class StagePhysics(unittest.TestCase):
    def test_free_fall_time_and_determinism(self):
        p = {"props": [{"id": "b", "type": "ball", "r": 0.1, "at": [0, 1.1, 0], "body": {"material": "stone"}}]}
        a, b = stage(p), stage(p)
        self.assertEqual(a, b)                                            # mọi worker mô phỏng ra cùng một kết quả
        want = math.sqrt(2 * 1.0 / 9.81) * 30                             # rơi 1 m (đáy bi) ở 30 fps ≈ 13.5 frame
        self.assertLessEqual(abs(first_impact(a, "b") - want), 1.0)
        self.assertAlmostEqual(a["pos"]["b"][-1][1], 0.1, delta=0.01)     # nằm yên trên sàn

    def test_hit_u_lands_impact_on_frame_even_with_slowmo(self):
        for phys in ({}, {"slowmo": [{"u": [0.45, 0.7], "rate": 0.25}]}):
            out = stage({"physics": phys, "props": [
                {"id": "b", "type": "bowling", "at": [0, 1.5, 0], "body": {"material": "stone", "hit_u": 0.5}}]}, 90)
            al = out["physics"]["aligned"][0]
            self.assertEqual(al["want"], 45)
            self.assertLessEqual(abs(al["got"] - al["want"]), 1, al)
        ball = {"id": "b", "type": "bowling", "at": [0, 3.5, 0], "body": {"material": "stone", "hit_u": 0.1}}
        out = stage({"props": [ball]}, 90)
        self.assertLess(out["physics"]["start"], 0)                       # rơi lâu hơn đoạn trước u → mô phỏng từ trước shot
        self.assertLess(out["pos"]["b"][0][1], 3.5)                       # frame đầu: vật đã đang rơi

    def test_resting_stack_and_feather(self):
        props = [{"id": f"k{i}", "type": "box", "size": [0.2, 0.2, 0.2], "at": [0, i * 0.2, 0], "body": {"material": "wood"}}
                 for i in range(4)]
        props += [{"id": "ball", "type": "ball", "r": 0.1, "at": [-0.8, 1.1, 0], "body": True},
                  {"id": "fe", "type": "feather", "at": [0.8, 1.1, 0], "body": {"material": "feather"}}]
        out = stage({"props": props}, 90)
        top = [q[1] for q in out["pos"]["k3"]]
        self.assertLess(max(top) - min(top), 0.01)                        # tháp đứng yên (chỉ lún < 1 cm)
        self.assertGreater(min(q[1] for q in out["pos"]["fe"][:30]), 0.5)  # lông vũ: 1 s mới rơi chưa tới nửa
        self.assertIsNone(first_impact(out, "fe"))                         # lông vũ đáp nhẹ: không cue, không kick

    def test_release_keeps_key_velocity_and_kinematic_pushes(self):
        out = stage({"physics": {"floor": False, "gravity": 0}, "props": [
            {"id": "t", "type": "ball", "r": 0.05, "at": [0, 1, 0], "keys": [{"u": 0.5, "at": [1, 1, 0], "ease": "linear"}],
             "body": {"release": 0.5}}]}, 61)
        xs = [q[0] for q in out["pos"]["t"]]
        self.assertAlmostEqual(xs[15], 0.5, delta=0.02)                   # trước release: đi đúng keyframe
        self.assertAlmostEqual(xs[60], 2.0, delta=0.08)                   # sau release: giữ vận tốc 1 m/0.5 s (g = 0)
        out = stage({"props": [
            {"id": "pusher", "type": "box", "size": [0.3, 0.3, 0.3], "at": [-1, 0, 0],
             "keys": [{"u": 1, "at": [0.6, 0, 0], "ease": "linear"}], "body": {"kind": "kinematic"}},
            {"id": "crate", "type": "box", "size": [0.2, 0.2, 0.2], "at": [0, 0, 0], "body": {"material": "wood"}}]}, 60)
        self.assertGreater(out["pos"]["crate"][-1][0], 0.3)               # kinematic theo key đẩy vật động đi
        self.assertAlmostEqual(out["pos"]["pusher"][-1][0], 0.6, delta=0.01)

    def test_impacts_make_cues_kicks_and_fx(self):
        out = stage({"physics": {"fx": "burst"}, "props": [
            {"id": "b", "type": "bowling", "at": [0, 1.5, 0], "body": {"material": "metal"}},
            {"id": "s", "type": "ball", "r": 0.08, "at": [0.6, 1.5, 0],
             "body": {"material": "rubber", "sfx": "pop", "fx": "splash"}},
            {"id": "q", "type": "ball", "r": 0.08, "at": [-0.6, 1.5, 0], "body": {"material": "rubber", "sfx": False}}]}, 60)
        names = {c["name"] for c in out["cues"]}
        self.assertIn("impact", names)                                    # thép 43 kg rơi 1.4 m → "impact"
        self.assertTrue(names <= {"impact", "pop", "thud", "thunk"}, names)
        imp = first_impact(out, "b")
        self.assertTrue(any(c["f"] == imp for c in out["cues"]))          # cue đúng frame chạm
        self.assertLessEqual(len(out["cues"]), 6)

    def test_no_physics_means_no_rapier(self):
        out = stage({"props": [{"id": "b", "type": "ball", "at": [0, 1, 0]}]}, 10)
        self.assertIsNone(out["physics"])


class PhysicsData(unittest.TestCase):
    def test_vocab_from_js_and_validator(self):
        voc = adapter.physics_vocab()
        self.assertTrue({"rubber", "metal", "wood", "feather"} <= set(voc["materials"]))
        self.assertEqual(voc["kinds"], ("dynamic", "fixed", "kinematic"))
        self.assertEqual(adapter.validate_three("stage", {"props": [{"type": "ball", "body": True}]}), [])
        errs = " ".join(adapter.validate_three("stage", {
            "physics": {"slowmo": [{"u": [0.7, 0.2]}], "fx": "dust"},
            "props": [{"type": "ball", "body": {"material": "jelly", "shape": "mesh", "hit_u": 2, "v": [1, 2]}},
                      {"type": "character", "body": True},
                      {"type": "box", "body": {"kind": "fixed", "release": 0.3}}]}))
        for frag in ("slowmo", "physics.fx", "jelly", "mesh", "hit_u", "body.v", "card 2D", "release/hit_u"):
            self.assertIn(frag, errs)

    def test_brief_documents_physics(self):
        from vidlib import brief
        t = brief._three_help()
        self.assertIn("PHYSICS", t)
        self.assertIn("hit_u", t)

    def test_rapier_vendored_and_pinned(self):
        p = os.path.join(ROOT, "vendor", "rapier", "rapier.mjs")
        with open(p, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest()[:16], "9f0c4ea949c1d632")
        with open(os.path.join(ROOT, "vendor", "rapier", "LICENSE"), encoding="utf-8") as fh:
            self.assertIn("Apache License", fh.read())


if __name__ == "__main__":
    unittest.main()
