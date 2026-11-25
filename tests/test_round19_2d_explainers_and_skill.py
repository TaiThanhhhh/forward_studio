"""Vòng 19 (PR-17): 2D Animated Explainer styles (Kurzgesagt/School of Life/Infographics), Director Skill & Poster QA."""
import os
import tempfile
import unittest

from engines import html
from vidlib import aireview, brief, director_skill, narratives, storyboard, styles, textstyle, viralscore
from vidlib.common import ROOT


def _kurzgesagt_2d_sb():
    return storyboard.normalize({
        "slug": "kurzgesagt-demo",
        "topic": "Why your immune system is secretly fighting a war right now",
        "title": "Your Immune System's Hidden War",
        "style": "kurzgesagt-black",
        "format_family": "illustrated_2d_explainer",
        "archetype": "forensic_dossier",
        "outro": {"mode": "loop", "bridge_frames": 8},
        "story_hud": {"kind": "meter", "label": "CELLS DEPLOYED", "from": 0, "to": 100, "unit": "%"},
        "shots": [
            {
                "id": "C01",
                "beat": "hook",
                "target_sec": 2.2,
                "mode": "code",
                "vo": "Every second, billions of microscopic soldiers patrol your bloodstream without you ever noticing.",
                "sfx": ["sub_drop"],
                "code": {
                    "engine": "html",
                    "scene": "scene",
                    "params": {
                        "title": "HIDDEN WAR",
                        "actors": [
                            {"id": "hero", "icon": "rig:adult:idle:neutral", "x": 0.35, "y": 0.65, "size": 220},
                            {"id": "cell", "icon": "cell", "x": 0.68, "y": 0.55, "size": 160, "role": "cold"},
                        ],
                    },
                },
            },
            {
                "id": "C02",
                "beat": "setup",
                "target_sec": 3.2,
                "mode": "code",
                "transition_in": "iris_match",
                "vo": "Because bacteria double every twenty minutes, a single cut could turn deadly fast.",
                "sfx": ["riser_long"],
                "code": {
                    "engine": "html",
                    "scene": "xray_cutaway",
                    "params": {"core_icon": "heart", "callout_num": "20 MIN", "callout_label": "DOUBLING TIME"},
                },
            },
            {
                "id": "C03",
                "beat": "escalate",
                "target_sec": 3.2,
                "mode": "code",
                "transition_in": "whip_match",
                "vo": "Yet macrophage guards swallow invaders whole and call backup across your veins.",
                "sfx": ["pop"],
                "code": {
                    "engine": "html",
                    "scene": "process",
                    "params": {
                        "steps": [
                            {"icon": "shield", "label": "Detect"},
                            {"icon": "bolt", "label": "Signal"},
                            {"icon": "check", "label": "Neutralize"},
                        ]
                    },
                },
            },
            {
                "id": "C04",
                "beat": "payoff",
                "target_sec": 3.0,
                "mode": "code",
                "transition_in": "tape_stop",
                "vo": "Instead of brute force, T-cells memorize the enemy's signature for decades.",
                "sfx": ["sting"],
                "code": {
                    "engine": "html",
                    "scene": "hero_stat",
                    "params": {"number": "10", "suffix": "B", "label": "UNIQUE RECEPTORS", "role": "accent"},
                },
            },
            {
                "id": "C05",
                "beat": "twist",
                "target_sec": 2.8,
                "mode": "code",
                "transition_in": "iris_match",
                "vo": "Which means your body already knows how to fight diseases it has never met, because...",
                "sfx": ["boom"],
                "code": {
                    "engine": "html",
                    "scene": "scene",
                    "params": {
                        "actors": [
                            {"id": "person", "icon": "rig:adult:cheer:happy", "x": 0.5, "y": 0.65, "size": 240},
                            {"id": "shield", "icon": "shield", "x": 0.5, "y": 0.4, "size": 140, "role": "accent"},
                        ],
                    },
                },
            },
        ],
    })


class TestRound19ExplainersAndSkill(unittest.TestCase):
    def test_three_new_2d_looks_and_styles_registered(self):
        for look_name in ("kurzgesagt", "schooloflife", "infographics"):
            self.assertIn(look_name, html.LOOKS)

        expected = {
            "kurzgesagt-black": "kurzgesagt",
            "school-of-life-black": "schooloflife",
            "infographics-show-black": "infographics",
        }
        av = styles.available()
        for sid, expected_look in expected.items():
            self.assertIn(sid, av)
            st = textstyle.load_style(sid)
            self.assertEqual(st["code_engine"], "html")
            self.assertEqual(st["html"]["look"], expected_look)
            self.assertTrue(os.path.isfile(os.path.join(ROOT, "assets", "fonts", st["font"])), sid)

    def test_illustrated_2d_explainer_format_and_viralscore(self):
        self.assertIn("illustrated_2d_explainer", narratives.format_ids())
        sb = _kurzgesagt_2d_sb()
        errs, _ = storyboard.validate(sb)
        self.assertEqual(errs, [])
        res = viralscore.score_storyboard(sb)
        self.assertEqual(res["format_family"], "illustrated_2d_explainer")
        self.assertGreaterEqual(
            res["total"], 90, f"2D explainer scored {res['total']} ({res['axes']}): {res['suggestions']}"
        )
        self.assertEqual(res["grade"], "S")

    def test_director_skill_loaded_in_brief_and_learn_appends(self):
        self.assertTrue(os.path.isfile(director_skill.SKILL_PATH))
        b = brief.build("Why anxiety hijacks focus", "anxiety-focus", plan={"style": "school-of-life-black"})
        self.assertIn("CHANNEL DIRECTOR SKILL", b)
        self.assertIn("Poster Rule", b)

        with tempfile.TemporaryDirectory() as tmp:
            sp = os.path.join(tmp, "DIRECTOR_SKILL.md")
            _, entry, added = director_skill.add_lesson("Tránh zoom chậm rì trên thẻ tĩnh.", category="2d", path=sp)
            self.assertTrue(added)
            self.assertIn("[2d", entry)
            # Duplicate lesson should not be appended twice
            _, _, added2 = director_skill.add_lesson("Tránh zoom chậm rì trên thẻ tĩnh.", category="2d", path=sp)
            self.assertFalse(added2)
            lessons = director_skill.list_lessons(path=sp)
            self.assertEqual(len(lessons), 1)

    def test_aireview_includes_poster_frame_and_anti_slop(self):
        prompt = aireview.build_prompt({"title": "Test 2D"})
        self.assertIn("poster_frame_score", prompt)
        self.assertIn("anti_slop_flags", prompt)
        self.assertIn("DIRECTOR_SKILL.md", prompt)
        self.assertIn("poster_frame_score", aireview.REVIEW_SCHEMA["properties"])
        self.assertIn("anti_slop_flags", aireview.REVIEW_SCHEMA["properties"])

        md = aireview.format_markdown(
            {
                "verdict": "READY",
                "clarity_score": 9,
                "muted_hook_score": 9,
                "visual_realism_score": 10,
                "pacing_score": 9,
                "poster_frame_score": 9,
                "anti_slop_flags": ["Không phát hiện"],
                "summary": "Đạt chuẩn poster.",
                "issues": [],
            },
            title="Test",
        )
        self.assertIn("Poster", md)
        self.assertIn("AI-Slop", md)


if __name__ == "__main__":
    unittest.main()
