"""lib/motion: bản Python phải cho cùng giá trị với bản JS (engine code-shot) — chạy JS bằng node nếu có."""
import json
import os
import shutil
import subprocess
import unittest

import lib.motion as m

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS = [0, 0.1, 0.24, 0.25, 0.4, 0.5, 0.77, 1.0, 1.3]
KEYS = [{"f": 0, "pos": [0, 1, 5], "look": [0, 1, 0], "fov": 40},
        {"f": 30, "pos": [2, 1.5, 4], "look": [0, 1.2, 0], "fov": 34, "roll": 3, "ease": "easeOut"},
        {"f": 60, "pos": [3, 2, 2], "look": [0, 1, 0], "fov": 30, "path": [[3, 1.8, 3.5]]}]
KICKS = [{"f": 40, "a": 0.1}]


def py_values():
    out = {}
    for name in ("smooth", "easeOut", "easeIn", "back", "anticip", "spring", "bounceOut", "elastic", "expoOut", "circOut",
                 "sine", "backIn", "steps"):
        out[name] = [m.EASE[name](t) for t in TS]
    out["cam"] = [m.cam_from_keys(KEYS, f, 0.0012, KICKS) for f in (-5, 0, 12, 30, 41, 44, 50, 60, 75)]
    out["spline"] = [m.spline([[0, 0, 0], [1, 2, 0], [3, 1, 1], [4, 0, 2]], u) for u in TS]
    out["idle"] = [m.idle(f, 3) for f in (0, 17, 99)]
    out["blink"] = [m.blink_at(f, 2) for f in range(0, 120, 7)]
    out["q"] = [m.q(x) for x in (0.125, 1.005, -0.335, 2.5)]
    return out


JS = """
import * as m from './lib/motion/motion.js';
const TS = %s, KEYS = %s, KICKS = %s;
const out = {};
for (const n of ['smooth','easeOut','easeIn','back','anticip','spring','bounceOut','elastic','expoOut','circOut',
                 'sine','backIn','steps'])
  out[n] = TS.map(t => m.M[n](t));
out.cam = [-5,0,12,30,41,44,50,60,75].map(f => { const c = m.camFromKeys(KEYS, f, {creep: 0.0012, kicks: KICKS});
  return {pos: c.pos, look: c.look, fov: c.fov, roll: c.roll || 0}; });
out.spline = TS.map(u => m.spline([[0,0,0],[1,2,0],[3,1,1],[4,0,2]], u));
out.idle = [0,17,99].map(f => m.idle(f, 3));
out.blink = Array.from({length: 18}, (_, i) => m.blinkAt(i*7, 2));
out.q = [0.125, 1.005, -0.335, 2.5].map(x => m.q(x));
console.log(JSON.stringify(out));
"""


class MotionLibTest(unittest.TestCase):
    def test_shapes(self):
        self.assertAlmostEqual(m.smooth(0.5), 0.5)
        self.assertGreater(max(m.back(t / 20) for t in range(21)), 1.0)      # back vượt quá 1
        self.assertLess(min(m.anticip(t / 20) for t in range(21)), 0.0)     # anticip lấy đà ngược
        self.assertAlmostEqual(m.spring(3.0), 1.0, places=4)                 # spring về 1
        for name in ("bounceOut", "elastic", "expoOut", "circOut", "sine", "backIn", "steps"):
            self.assertAlmostEqual(m.EASE[name](0), 0.0, places=6, msg=name)  # mọi easing đi từ 0 tới 1
            self.assertAlmostEqual(m.EASE[name](1), 1.0, places=6, msg=name)
        self.assertGreater(max(m.elastic(t / 40) for t in range(41)), 1.0)  # elastic vượt quá
        self.assertLess(min(m.back_in(t / 40) for t in range(41)), 0.0)     # backIn lùi lấy đà
        self.assertEqual(len({m.steps(t / 40) for t in range(41)}), 6)       # 5 bậc + đích
        self.assertEqual(m.kick_at(10, [{"f": 10, "a": 0.1}]), 0.1)
        self.assertEqual(m.kick_at(17, [{"f": 10, "a": 0.1}]), 0.0)         # đúng 7 frame
        c0, c1 = m.cam_from_keys(KEYS, 70), m.cam_from_keys(KEYS, 71)
        self.assertLess(c1["fov"], c0["fov"])                                # giữ khung vẫn creep

    @unittest.skipUnless(shutil.which("node"), "cần node để chạy bản JS")
    def test_js_parity(self):
        code = JS % (json.dumps(TS), json.dumps(KEYS), json.dumps(KICKS))
        r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        js = json.loads(r.stdout)
        py = json.loads(json.dumps(py_values()))

        def close(a, b, path):
            if isinstance(a, dict):
                for k in a:
                    close(a[k], b[k], f"{path}.{k}")
            elif isinstance(a, list):
                self.assertEqual(len(a), len(b), path)
                for i, (x, y) in enumerate(zip(a, b)):
                    close(x, y, f"{path}[{i}]")
            else:
                self.assertAlmostEqual(float(a), float(b), places=9, msg=path)
        close(py, js, "motion")


if __name__ == "__main__":
    unittest.main()
