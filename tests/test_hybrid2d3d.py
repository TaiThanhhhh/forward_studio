# ruff: noqa: E501 — harness JS nhúng cho Node test
"""Vòng 10 · WP-X: Hybrid 2D ↔ 3D (card2d, multiplane, overlay2d, hậu kỳ 3D theo look 2D, nối `do: [{verb}]` vào stage.js)."""
import json
import os
import shutil
import subprocess
import unittest

from engines import adapter
from vidlib import motionplan

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def node(js):
    r = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", check=True, timeout=120)
    return json.loads(r.stdout.strip().splitlines()[-1])


class TestHybridValidation(unittest.TestCase):
    def test_validate_card2d_multiplane_overlay2d_and_do(self):
        ok = {
            "set": "meadow",
            "props": [
                {"id": "dog1", "type": "dachshund", "gait": "sniff", "do": [{"u": 0.2, "verb": "hop", "args": {"h": 0.5}}]},
                {"id": "c1", "type": "card2d", "draw": "rig:cat", "look": "pixel16", "billboard": True},
                {"id": "mp", "type": "multiplane", "layers": [
                    {"draw": "tree", "z": -0.6, "look": "cutout"},
                    {"draw": "rig:dog", "z": 0.0, "look": "cutout"},
                ]},
            ],
            "overlay2d": [{"text": "300M receptors", "of": "dog1", "z": "front"}],
        }
        self.assertEqual(adapter.validate_three("stage", ok), [])

    def test_validate_rejects_bad_hybrid_params(self):
        bad = {
            "props": [
                {"id": "d", "type": "dog", "do": [{"u": 0.1, "verb": "teleport_xyz"}]},
                {"id": "mp", "type": "multiplane", "layers": []},
            ],
            "overlay2d": [{"text": "Hi", "of": "missing_id", "z": "middle"}],
        }
        errs = adapter.validate_three("stage", bad)
        txt = "\n".join(errs)
        self.assertIn("teleport_xyz", txt)
        self.assertIn("multiplane", txt)
        self.assertIn("missing_id", txt)
        self.assertIn("front", txt)

    def test_motionplan_detects_three_verb_support(self):
        sup = motionplan.verb_support()
        self.assertTrue(sup["html"])
        self.assertTrue(sup["three"])


@unittest.skipUnless(shutil.which("node"), "cần node")
class TestHybridNode(unittest.TestCase):
    def test_card2d_multiplane_and_do_verbs_in_stage(self):
        js = """
        import * as THREE from './vendor/three/three.module.js';
        import * as MO from './lib/motion/motion.js';
        import * as PROPS from './engines/three/props.js';
        import * as CAST from './engines/three/cast.js';
        import { build } from './engines/three/scenes/stage.js';
        const world = new THREE.Group();
        const mkctx = (N) => ({ THREE, MO, PROPS, CAST, world, N, fps: 30,
          job: { font_family: 'sans-serif', world: { colors: { white: '#fff', accent: '#ffd23f' } } },
          C: (k) => k, toon: () => new THREE.MeshBasicMaterial(), flat: () => new THREE.MeshBasicMaterial(),
          glow: (c, s, p = world) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial()); p.add(m); return m; },
          add: (geo, m, x = 0, y = 0, z = 0, p = world) => { const me = new THREE.Mesh(geo, typeof m === 'string' ? new THREE.MeshBasicMaterial() : m); me.position.set(x, y, z); p.add(me); return me; },
          group: (p = world, x = 0, y = 0, z = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); p.add(g); return g; } });
        const s = build(mkctx(60), {
          props: [
            { id: 'c', type: 'card2d', draw: 'rig:dog', look: 'pixel16', at: [0, 0, 0], do: [{ u: 0, verb: 'hop', dur: 0.5, args: { h: 0.8 } }] },
            { id: 'm', type: 'multiplane', layers: [{ draw: 'tree', z: -0.5 }, { draw: 'flower', z: 0.2 }] },
          ],
          overlay2d: [{ text: 'HD-2D', of: 'c', z: 'front' }],
        });
        s.frame(0); const y0 = s.objectOf('c').position.y;
        s.frame(7); const y7 = s.objectOf('c').position.y;
        console.log(JSON.stringify({ y0: Math.round(y0 * 1000) / 1000, y7: Math.round(y7 * 1000) / 1000,
          mpChildren: s.objectOf('m').children.length, texts: s.texts }));
        """
        o = node(js)
        self.assertGreater(o["y7"], o["y0"] + 0.1)          # verb `hop` nâng prop 3D lên
        self.assertEqual(o["mpChildren"], 2)                # 2 lớp cắt giấy multiplane
        self.assertIn("HD-2D", o["texts"])                  # overlay2d đưa chữ vào meta.texts


if __name__ == "__main__":
    unittest.main()
