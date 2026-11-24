"""Vòng 16 (PR-12) — 3D Studio Softbox IBL & literal Tech/AI beats (`code_terminal`, `chat_prompt`)."""
import json
import os
import subprocess
import unittest

from engines import html
from vidlib import storyboard, viralscore
from vidlib.common import ROOT


class Round16VisualUpgradesTests(unittest.TestCase):
    def test_code_terminal_and_chat_prompt_registered_and_valid(self):
        self.assertIn("code_terminal", html.BEATS)
        self.assertIn("chat_prompt", html.BEATS)
        demo = json.loads(open(os.path.join(ROOT, "engines", "html", "demo.json"), encoding="utf-8").read())
        self.assertEqual(html.validate("code_terminal", demo["code_terminal"]), [])
        self.assertEqual(html.validate("chat_prompt", demo["chat_prompt"]), [])
        self.assertTrue(html.validate("code_terminal", {}))
        self.assertTrue(html.validate("chat_prompt", {"user": "hi"}))

    def test_new_beats_render_safely_in_node_mock_canvas(self):
        script = r"""
import { BEATS } from './engines/html/beats.js';
import fs from 'node:fs';
const demo = JSON.parse(fs.readFileSync('./engines/html/demo.json', 'utf8'));
const g = {
  save(){}, restore(){}, translate(){}, scale(){}, rotate(){}, beginPath(){}, rect(){}, arc(){},
  fill(){}, stroke(){}, fillRect(){}, moveTo(){}, lineTo(){}, setLineDash(){},
  fillStyle: '', strokeStyle: '', lineWidth: 1, globalAlpha: 1,
};
const ctx = {
  W: 1080, H: 1920, N: 90, f: 50, TAU: Math.PI * 2, g,
  A: { x0: 65, x1: 940, top: 270, bottom: 1240, cx: 502 },
  EASE: { out: (x) => x, back: (x) => x },
  clamp: (x) => Math.max(0, Math.min(1, x)),
  lerp: (a, b, t) => a + (b - a) * t,
  k: () => 1,
  col: () => '#FFFFFF',
  fmtNum: (v) => String(v),
  text: () => ({ x0: 100, y0: 100, x1: 400, y1: 140, size: 32, lines: 1 }),
  K: { header: () => 340, tag: () => {} },
};
for (const name of ['code_terminal', 'chat_prompt']) {
  const b = BEATS[name](ctx, demo[name]);
  if (!Array.isArray(b.texts) || b.texts.length === 0) throw new Error(name + ' missing texts');
  b.draw(ctx);
}
console.log('OK_NODE_BEATS');
"""
        r = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK_NODE_BEATS", r.stdout)

    def test_three_studio_softbox_and_literal_visual_law_present(self):
        main_js = open(os.path.join(ROOT, "engines", "three", "main.js"), encoding="utf-8").read()
        self.assertIn("PMREMGenerator", main_js)
        self.assertIn("#fff6eb", main_js)
        brief_md = open(os.path.join(ROOT, "prompts", "storyboard_brief.md"), encoding="utf-8").read()
        self.assertIn("Literal Visual Law", brief_md)

    def test_fast_tech_autopsy_with_new_beats_scores_high(self):
        sb = storyboard.normalize({
            "topic": "Why AI can't count R's in strawberry",
            "style": "hud-black",
            "format_family": "fast_tech_autopsy",
            "archetype": "myth_autopsy",
            "outro": {"mode": "loop", "bridge_frames": 8},
            "shots": [
                {
                    "id": "C01", "beat": "hook", "target_sec": 2.2, "mode": "code",
                    "vo": "Ask AI how many R's are in strawberry and watch it fail.",
                    "sfx": ["sub_drop"],
                    "code": {"engine": "html", "scene": "chat_prompt", "params": {
                        "user": "How many R's in strawberry?", "ai": "There are 2.", "verdict": "WRONG: 3",
                    }},
                },
                {
                    "id": "C02", "beat": "escalate", "target_sec": 3.4, "mode": "code", "transition_in": "tape_stop",
                    "vo": "Because AI never sees letters—it chops words into numeric tokens.",
                    "sfx": ["tape_stop", "riser_long"],
                    "code": {"engine": "html", "scene": "code_terminal", "params": {
                        "filename": "tokenizer.py",
                        "lines": ["encode('strawberry')", {"text": "[496, 675, 15717]", "bug": True}],
                        "tokens": [{"text": "str", "id": 496}, {"text": "aw", "id": 675}, {"text": "berry", "id": 15717}],
                    }},
                },
                {
                    "id": "C03", "beat": "payoff", "target_sec": 3.4, "mode": "code", "transition_in": "whip_match",
                    "vo": "Instead of spelling, three numbers run four times faster inside a GPU.",
                    "sfx": ["hit"],
                    "code": {"engine": "three", "scene": "stage", "params": {
                        "props": [{"type": "chip"}], "frame": {"preset": "low_hero"},
                    }},
                },
                {
                    "id": "C04", "beat": "twist", "target_sec": 3.2, "mode": "code", "transition_in": "iris_match",
                    "vo": "Yet without letters, it's blind to spelling, which is why when you...",
                    "sfx": ["sting"],
                    "code": {"engine": "three", "scene": "stage", "params": {
                        "props": [{"type": "laptop"}], "frame": {"preset": "dolly_zoom"},
                    }},
                },
            ],
        })
        res = viralscore.score_storyboard(sb)
        self.assertGreaterEqual(
            res["total"], 90, f"Tech autopsy scored {res['total']} ({res['axes']}): {res['suggestions']}"
        )


if __name__ == "__main__":
    unittest.main()
