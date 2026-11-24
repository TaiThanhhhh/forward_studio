"""Kiểm thử toàn diện Vòng 12 (WP-1..WP-6): mỹ thuật người lớn & đồng bộ 2D↔3D, chống chồng chữ & Grid 3 tầng,
auto-captions studio_clean, cơ chế đúng vật lý & Clutter Linter, nhịp thở trưởng thành, và cổng QA ĐỎ."""
import json
import os
import unittest

import numpy as np
from PIL import Image

import studio
from engines import html
from vidlib import autocaptions, brief, codeshot, linter, motionplan, qagate, qareport, vo
from vidlib.common import CONFIG_DIR, ROOT, channel


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def _sample_vo():
    return {
        "lines": [
            {
                "words": [
                    {"w": "Humans", "start": 0.0, "end": 0.25},
                    {"w": "cool", "start": 0.26, "end": 0.50},
                    {"w": "themselves", "start": 0.51, "end": 0.90},
                    {"w": "through", "start": 0.91, "end": 1.20},
                    {"w": "sweat.", "start": 1.21, "end": 1.60},
                ]
            }
        ]
    }


class Round12Tests(unittest.TestCase):
    # ---- WP-1: Adult Editorial Art & 2D/2.5D/3D Sync ----
    def test_wp1_design_system_and_character_style(self):
        self.assertEqual(codeshot.character_style_of("vox-editorial-black"), "editorial")
        self.assertEqual(codeshot.character_style_of("flat-vector-black"), "editorial")
        self.assertEqual(codeshot.character_style_of("cartoon-story-black"), "cartoon")
        self.assertEqual(codeshot.character_style_of("retro90-lowpoly-black"), "cartoon")

        w, _ = codeshot.world("vox-editorial-black")
        self.assertEqual(w.get("character_style"), "editorial")
        ds = w.get("design_system") or {}
        for tok in ("actor_a", "actor_b", "actor_neutral", "heat_glow"):
            self.assertIn(tok, ds)
            self.assertIn(tok, w["colors"])

    def test_wp1_editorial_and_heat_hooks_in_engines(self):
        rig_js = _read("engines", "html", "rig2d.js")
        cre_js = _read("engines", "three", "creatures.js")
        props_js = _read("engines", "three", "props.js")
        looks_js = _read("engines", "html", "looks.js")
        self.assertIn("thermalCore", rig_js)
        self.assertIn("editorial", rig_js)
        self.assertIn("EDITORIAL_TONES", cre_js)
        self.assertIn("heat:", cre_js)
        self.assertIn("setHeat", props_js)
        self.assertIn("editorialGrid", looks_js)

    # ---- WP-2: Zero-Overlap 2D Layout & 3-Zone Grid ----
    def test_wp2_core_and_beats_layout_contracts(self):
        core_js = _read("engines", "html", "core.js")
        beats_js = _read("engines", "html", "beats.js")
        self.assertIn("window.overlapPairs", core_js)
        self.assertIn("autoNudge", core_js)
        self.assertIn("JOB.layout_grid", core_js)
        self.assertIn("STAGE_BOTTOM", core_js)
        self.assertNotIn("cy + 250", beats_js)
        self.assertIn("fitText", beats_js)
        self.assertIn("'heat'", beats_js)
        self.assertIn("heat", html.PARAMS["scene"][1])

    # ---- WP-3: Smart Studio Auto-Captions ----
    def test_wp3_studio_clean_preset_zone_c_and_suppression(self):
        self.assertEqual(autocaptions.PRESETS[0], "studio_clean")
        sample = _sample_vo()
        layer = autocaptions.Layer(sample, preset="studio_clean", style="vox-editorial-black")
        base = Image.new("RGB", (1080, 1920), (11, 13, 17))
        out = layer.draw(base.copy(), 0.35, shot={"id": "C02", "beat": "escalate", "code": {"scene": "scene"}})
        diff = np.abs(np.asarray(out, np.int16) - np.asarray(base, np.int16)).sum(axis=2)
        self.assertEqual(int(diff[:1260, :].sum()), 0, "studio_clean không được vẽ vào Zone B (y < 1260)")
        self.assertGreater(int(diff[1300:1500, :].sum()), 5000, "studio_clean phải vẽ trong Zone C")
        self.assertTrue(layer.last_draw_info and not layer.last_draw_info.get("suppressed"))

        # Smart suppression trên fact & title:kinetic
        fact_shot = {"id": "C09", "beat": "twist", "code": {"scene": "fact", "params": {"layout": "flip"}}}
        title_shot = {"id": "C01", "beat": "hook", "code": {"scene": "title", "params": {"layout": "kinetic"}}}
        self.assertTrue(autocaptions.should_suppress(fact_shot))
        self.assertTrue(autocaptions.should_suppress(title_shot))
        sup = layer.draw(base.copy(), 0.35, shot=fact_shot)
        self.assertTrue(np.array_equal(np.asarray(sup), np.asarray(base)))

        # Smart vertical nudge né thanh sáng nằm đúng tâm cy = 1395
        busy = base.copy()
        arr = np.asarray(busy).copy()
        arr[1365:1425, 160:920] = (235, 235, 235)
        busy_img = Image.fromarray(arr)
        layer2 = autocaptions.Layer(sample, preset="studio_clean", style="vox-editorial-black")
        layer2.draw(busy_img, 0.35, shot={"id": "C05", "beat": "escalate", "code": {"scene": "stage"}})
        self.assertIsNotNone(layer2.last_draw_info)
        self.assertNotEqual(layer2.last_draw_info.get("cy"), 1395)

    # ---- WP-4: Grounded Metaphors, Visual Budget & Clutter Linter ----
    def test_wp4_clutter_linter_catches_crowded_and_passes_lean(self):
        crowded = {
            "shots": [
                {
                    "id": "C03",
                    "beat": "escalate",
                    "code": {
                        "scene": "scene",
                        "params": {
                            "kicker": "HEAT",
                            "title": "Why Runners Overheat Fast",
                            "actors": [{"id": f"a{i}", "icon": "dot", "x": 0.5, "y": 0.5} for i in range(6)],
                            "labels": [{"text": f"Label {i} extra words"} for i in range(4)],
                        },
                    },
                },
                {
                    "id": "C04",
                    "beat": "escalate",
                    "code": {
                        "scene": "stage",
                        "params": {
                            "props": [{"id": f"p{i}", "type": "box"} for i in range(7)],
                        },
                    },
                },
            ]
        }
        issues = linter.lint_clutter(crowded)
        wheres = {i["where"] for i in issues}
        self.assertIn("C03", wheres)
        self.assertIn("C04", wheres)
        self.assertGreaterEqual(len(issues), 3)

        lean = {
            "shots": [
                {
                    "id": "C02",
                    "beat": "escalate",
                    "code": {
                        "scene": "scene",
                        "params": {
                            "actors": [
                                {"id": "runner", "icon": "runner", "heat": 0.8},
                                {"id": "d1", "icon": "drop"},
                                {"id": "bg", "icon": "dot", "z": 2.4},
                            ],
                            "labels": [{"text": "41.2°C", "of": "runner"}],
                        },
                    },
                }
            ]
        }
        self.assertEqual(linter.lint_clutter(lean), [])

    def test_wp4_metaphors_and_brief_and_stage(self):
        for mid in ("sweat_cooling", "core_temperature", "lactic_burn", "oxygen_delivery"):
            m = motionplan.get(mid)
            self.assertIsNotNone(m, mid)
            self.assertEqual(motionplan.entry_errors(m), [], mid)
            actors = ((m.get("recipe") or {}).get("params") or {}).get("actors") or []
            self.assertLessEqual(len(actors), 3, f"{mid} vượt quá 3 actor")
            self.assertFalse(any(a.get("icon") == "thermo" for a in actors), f"{mid} vẫn còn nhiệt kế trôi nổi")
        self.assertIn("heat", motionplan.CREATURE_KEYS)
        help_txt = brief.mix_help()
        self.assertIn("VISUAL BUDGET & STORYTELLING RULES", help_txt)
        self.assertIn("heat: 0..1", help_txt)
        stage_js = _read("engines", "three", "scenes", "stage.js")
        self.assertIn("footroom", stage_js)
        self.assertIn("heat:", stage_js)

    # ---- WP-5: Adult Pacing & 3-Zone Channel Config ----
    def test_wp5_channel_config_and_vo_pauses(self):
        cfg = channel()
        grid = cfg.get("layout_grid") or {}
        self.assertEqual(grid.get("header"), [250, 370])
        self.assertEqual(grid.get("stage"), [390, 1240])
        self.assertEqual(grid.get("captions"), [1340, 1460])
        self.assertEqual(cfg["vo"]["target_wps"], 3.0)
        self.assertLessEqual(cfg["vo"]["speed_max"], 1.08)
        self.assertEqual(cfg["captions"]["preset"], "studio_clean")
        self.assertIn("không chồng chữ", cfg["qa"]["blocking"])

        # Nhịp thở tự nhiên dài hơn trước payoff/twist
        p_same = vo.boundary_pause("escalate", "escalate")
        p_twist = vo.boundary_pause("payoff", "twist")
        p_payoff = vo.boundary_pause("escalate", "payoff")
        self.assertGreater(p_payoff, p_same)
        self.assertGreater(p_twist, p_same)

        # CLI --captions chấp nhận studio_clean
        args = studio.video_parser().parse_args(["demo", "--captions", "studio_clean"])
        self.assertEqual(args.captions, "studio_clean")

        # Schema mẫu đặt mặc định studio_clean
        with open(os.path.join(CONFIG_DIR, "..", "prompts", "storyboard_schema.json"), encoding="utf-8") as fh:
            schema = json.load(fh)
        self.assertEqual(schema.get("captions"), "studio_clean")

    # ---- WP-6: Red Text-Overlap QA Gate & Studio Checks ----
    def test_wp6_red_overlap_gate_and_studio_checks(self):
        self.assertEqual(qagate.level("không chồng chữ (text overlap)", False), "red")
        self.assertEqual(qagate.level("không chồng chữ (text overlap)", True), "green")

        # Cố tình tạo 2 khung chữ đè nhau → ĐỎ chặn xuất bản
        bad_ocr = {
            "overlaps": [],
            "boxes": [
                {"sid": "C08", "frame": 45, "text": "LONG FACT LINE", "box": [120, 700, 920, 920]},
                {"sid": "C08", "frame": 45, "text": "EMPHASIS", "box": [220, 820, 820, 960]},
                {"sid": "C03", "frame": 30, "text": "LOW TAG", "box": [300, 1260, 780, 1360]},
            ],
        }
        checks = qareport.studio_checks({"shots": []}, bad_ocr, captions_on=True)
        rows = qagate.classify(checks)
        summary = qagate.summary(rows)
        self.assertEqual(summary["verdict"], "red")
        self.assertTrue(any(r["label"].startswith("không chồng chữ") and r["level"] == "red" for r in rows))
        self.assertTrue(any(r["label"].startswith("phụ đề tách vùng hình") and r["level"] == "yellow" for r in rows))

        # Shot sạch: 0 chồng chữ, nằm trên y=1240, không rối → XANH 100%
        good_ocr = {
            "overlaps": [],
            "boxes": [
                {"sid": "C02", "frame": 30, "text": "41.2°C", "box": [380, 500, 700, 580]},
                {"sid": "C02", "frame": 30, "text": "CORE HEAT", "box": [360, 1080, 720, 1140]},
            ],
        }
        good_checks = qareport.studio_checks({"shots": [{"id": "C02", "code": {"scene": "scene", "params": {}}}]},
                                             good_ocr, captions_on=True)
        self.assertEqual(qagate.verdict(qagate.classify(good_checks)), "green")


if __name__ == "__main__":
    unittest.main()
