"""Kiểm thử toàn diện Vòng 13 (WP-1..WP-6):
- WP-1: 3 beat điện ảnh 2D (dossier, xray_cutaway, hero_stat), story_hud & editorialStageGlow.
- WP-2: 5 góc máy 3D điện ảnh, volumetricSpotlight & setClearColor sau setRenderTarget.
- WP-3: chuyển cảnh Agency (iris_match, whip_match, tape_stop) & seamless loop (outro.mode == "loop").
- WP-4: 5 mood nhạc musicgen (tất định, phổ khác biệt, dead-air drop) & 6 SFX Agency không clip.
- WP-5: 6 Director Archetypes xoay vòng chống lặp & brief.build nhúng luật Viral + archetype.
- WP-6: viralscore.score_storyboard (PowerPoint < 60 vs Agency ≥ 85), motionplan, linter & qareport.
"""
import json
import os
import tempfile
import unittest
from unittest import mock

import numpy as np

from engines import html
from vidlib import brief, linter, motionplan, musicgen, narratives, qareport, sfx, storyboard, viralscore
from vidlib.common import CONFIG_DIR, ROOT


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def _boring_powerpoint_sb():
    """Kịch bản PowerPoint nhạt: toàn thẻ phẳng title/fact/counter/compare, cắt cut, lời giáo khoa tuyến tính."""
    return {
        "topic": "Why running makes you sweat",
        "title": "Running and Sweat",
        "style": "vox-editorial-black",
        "language": "en",
        "outro": {"enabled": True, "mode": "code", "teaser": "Next topic"},
        "shots": [
            {
                "id": "C01",
                "beat": "hook",
                "mode": "code",
                "target_sec": 3.5,
                "transition_in": "cut",
                "vo": "Today we will talk about running and how your body cools down when you exercise outside.",
                "code": {"engine": "html", "scene": "title", "params": {"title": "Running and Sweat"}},
            },
            {
                "id": "C02",
                "beat": "setup",
                "mode": "code",
                "target_sec": 3.5,
                "transition_in": "cut",
                "vo": "First your leg muscles produce heat as they contract during a normal morning jog.",
                "code": {"engine": "html", "scene": "fact", "params": {"text": "Muscles make heat"}},
            },
            {
                "id": "C03",
                "beat": "escalate",
                "mode": "code",
                "target_sec": 3.5,
                "transition_in": "cut",
                "vo": "Then your sweat glands release water onto the surface of your warm skin.",
                "code": {"engine": "html", "scene": "counter", "params": {"to": 2, "unit": "liters"}},
            },
            {
                "id": "C04",
                "beat": "escalate",
                "mode": "code",
                "target_sec": 3.5,
                "transition_in": "cut",
                "vo": "Next that liquid evaporates into the air around you as you keep moving forward.",
                "code": {"engine": "html", "scene": "compare", "params": {
                    "left": {"label": "Walk", "value": 1, "icon": "person"},
                    "right": {"label": "Run", "value": 3, "icon": "runner"},
                }},
            },
            {
                "id": "C05",
                "beat": "payoff",
                "mode": "code",
                "target_sec": 3.5,
                "transition_in": "cut",
                "vo": "Finally drinking water helps replace the fluid you lost during your long run.",
                "code": {"engine": "html", "scene": "fact", "params": {"text": "Drink water often"}},
            },
            {
                "id": "C06",
                "beat": "twist",
                "mode": "code",
                "target_sec": 3.5,
                "transition_in": "cut",
                "vo": "And that is how perspiration keeps humans comfortable in summer weather.",
                "code": {"engine": "html", "scene": "title", "params": {"title": "Stay Hydrated"}},
            },
        ],
    }


def _agency_viral_sb():
    """Kịch bản chuẩn Agency Viral Vòng 13: archetype, story_hud, 3 beat mới, 3D multi-preset, match cuts, loop."""
    return {
        "topic": "Your mouth can feed your brain before fuel arrives",
        "title": "The Carb Rinse Paradox",
        "style": "vox-editorial-black",
        "language": "en",
        "archetype": "forensic_dossier",
        "story_hud": {
            "kind": "clock",
            "label": "TIME TRIAL",
            "from": 0,
            "to": 60,
            "unit": "MIN",
            "role": "accent",
        },
        "outro": {"enabled": True, "mode": "loop", "bridge_frames": 8},
        "shots": [
            {
                "id": "C01",
                "beat": "hook",
                "mode": "code",
                "target_sec": 2.0,
                "transition_in": "cut",
                "sfx": ["sub_drop"],
                "vo": "Spitting out sugar still makes you run faster.",
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {
                        "set": "track",
                        "frame": {"preset": "ecu_macro"},
                        "props": [{"id": "r1", "type": "runner3d", "pose": "sprint"}],
                    },
                },
            },
            {
                "id": "C02",
                "beat": "setup",
                "mode": "code",
                "target_sec": 3.2,
                "transition_in": "whip_match",
                "sfx": ["paper_rustle", "swish_match"],
                "vo": "Cyclists swished a carb drink for five seconds, yet swallowed zero calories.",
                "code": {
                    "engine": "html",
                    "scene": "dossier",
                    "params": {
                        "tag": "CASE // 09-B",
                        "headline": "Mouth sensors fire before glucose arrives",
                        "highlight": "before glucose",
                        "evidence": [
                            {"k": "RINSE", "v": "5 sec carb swish"},
                            {"k": "SWALLOWED", "v": "0.0 g sugar"},
                        ],
                        "stamp": "VERIFIED",
                    },
                },
            },
            {
                "id": "C03",
                "beat": "escalate",
                "mode": "code",
                "target_sec": 3.4,
                "transition_in": "iris_match",
                "sfx": ["neural_pulse", "swish_match"],
                "vo": "Instead of waiting on digestion, oral receptors send an urgent wire straight upward.",
                "code": {
                    "engine": "html",
                    "scene": "xray_cutaway",
                    "params": {
                        "shell_icon": "person",
                        "core_icon": "brain",
                        "pulse_rate": 148,
                        "flow": [{"from": [-0.6, 0.2], "via": [-0.1, -0.2], "to": [0.4, -0.5], "count": 8}],
                        "callout_num": "0.4s",
                        "callout_label": "Neural relay",
                    },
                },
            },
            {
                "id": "C04",
                "beat": "escalate",
                "mode": "code",
                "target_sec": 3.2,
                "transition_in": "tape_stop",
                "sfx": ["tape_stop"],
                "vo": "But sweet fake sugar never triggers it, because your tongue detects real carbs.",
                "code": {
                    "engine": "html",
                    "scene": "hero_stat",
                    "params": {
                        "kicker": "TIME TRIAL GAIN",
                        "number": 2.9,
                        "prefix": "+",
                        "suffix": "%",
                        "unit": "FASTER OUTPUT",
                        "label": "Zero calories swallowed",
                        "bg_motif": "rings",
                    },
                },
            },
            {
                "id": "C05",
                "beat": "escalate",
                "mode": "code",
                "target_sec": 3.4,
                "transition_in": "whip_match",
                "sfx": ["riser_long"],
                "vo": "That signal forces your motor cortex to release hidden power reserves immediately.",
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {
                        "set": "stadium",
                        "frame": {"preset": "low_hero"},
                        "props": [{"id": "r2", "type": "runner3d", "pose": "sprint", "heat": 0.7}],
                    },
                },
            },
            {
                "id": "C06",
                "beat": "payoff",
                "mode": "code",
                "target_sec": 3.0,
                "transition_in": "iris_match",
                "sfx": ["sub_drop", "hit"],
                "vo": "So exhaustion isn't empty muscles, it's a cautious governor protecting your brain.",
                "code": {
                    "engine": "html",
                    "scene": "scene",
                    "params": {
                        "actors": [
                            {"id": "brain", "icon": "brain", "x": 0.5, "y": 0.42, "z": 0},
                            {"id": "runner", "icon": "runner", "x": 0.5, "y": 0.68, "z": 0.8},
                        ],
                    },
                },
            },
            {
                "id": "C07",
                "beat": "twist",
                "mode": "code",
                "target_sec": 2.8,
                "transition_in": "cut",
                "sfx": ["sting"],
                "vo": "Until you trick that governor, which is why merely...",
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {
                        "set": "track",
                        "frame": {"preset": "tracking_low"},
                        "props": [{"id": "r3", "type": "runner3d", "pose": "run"}],
                    },
                },
            },
        ],
    }


class Round13Tests(unittest.TestCase):
    # ---- WP-1: Cinema 2D Beats, Persistent Story HUD & Atmospheric Craft ----
    def test_wp1_cinema_beats_registered_and_valid(self):
        demo_path = os.path.join(ROOT, "engines", "html", "demo.json")
        with open(demo_path, encoding="utf-8") as fh:
            demo_data = json.load(fh)
        for beat in ("dossier", "xray_cutaway", "hero_stat"):
            self.assertIn(beat, html.BEATS, f"{beat} thiếu trong html.BEATS")
            self.assertIn(beat, html.PARAMS, f"{beat} thiếu trong html.PARAMS")
            self.assertIn(beat, demo_data, f"{beat} thiếu trong demo.json")
            self.assertEqual(html.validate(beat, demo_data[beat]), [], f"{beat} demo không hợp lệ")

        # Validate catches invalid params cleanly
        self.assertTrue(html.validate("dossier", {}))
        self.assertTrue(html.validate("xray_cutaway", {"core_icon": "heart", "pulse_rate": 999}))
        self.assertTrue(html.validate("hero_stat", {"number": 5, "bg_motif": "unknown_motif"}))

    def test_wp1_story_hud_and_editorial_stage_glow_hooks(self):
        core_js = _read("engines", "html", "core.js")
        looks_js = _read("engines", "html", "looks.js")
        self.assertIn("story_hud", core_js)
        self.assertIn("editorialStageGlow", looks_js)

    # ---- WP-2: 3D Cinema Lighting & 5 Camera Presets ----
    def test_wp2_camera_presets_spotlight_and_clear_color_order(self):
        stage_js = _read("engines", "three", "scenes", "stage.js")
        props_js = _read("engines", "three", "props.js")
        main_js = _read("engines", "three", "main.js")
        for preset in ("ecu_macro", "low_hero", "tracking_low", "over_shoulder", "dolly_zoom"):
            self.assertIn(preset, stage_js, f"Thiếu preset camera 3D '{preset}' trong stage.js")
        self.assertIn("volumetricSpotlight", props_js)
        # Ensure setClearColor is called AFTER setRenderTarget in main.js render loop
        idx_rt = main_js.find("renderer.setRenderTarget(rtColor)")
        self.assertGreater(idx_rt, 0)
        snippet = main_js[idx_rt : idx_rt + 120]
        self.assertIn("renderer.setClearColor", snippet)

    # ---- WP-3: Agency Transitions & Seamless Loop Contract ----
    def test_wp3_agency_transitions_and_loop_outro_validate(self):
        for trans in ("iris_match", "whip_match", "tape_stop"):
            sb = storyboard.normalize({
                "topic": "Loop and match cut test",
                "outro": {"enabled": True, "mode": "loop", "bridge_frames": 8},
                "shots": [
                    {
                        "id": "C01",
                        "beat": "hook",
                        "mode": "code",
                        "target_sec": 2.0,
                        "transition_in": trans,
                        "code": {"engine": "html", "scene": "hero_stat", "params": {"number": 42, "label": "Test"}},
                    }
                ],
            })
            errs, _ = storyboard.validate(sb)
            self.assertEqual(errs, [], f"storyboard.validate từ chối transition '{trans}' hoặc outro.mode='loop': {errs}")

    # ---- WP-4: 5 Music Moods & 6 Agency SFX ----
    def test_wp4_music_moods_distinct_deterministic_and_dead_air(self):
        expected_moods = (
            "investigative_pulse",
            "kinetic_editorial",
            "visceral_thriller",
            "clockwork_tension",
            "minimal_cinematic",
        )
        self.assertEqual(tuple(musicgen.MOODS), expected_moods)
        rendered = {}
        for mood in expected_moods:
            a = musicgen.bed(6.0, stop_at=4.5, bpm=116, seed=13, mood=mood)
            b = musicgen.bed(6.0, stop_at=4.5, bpm=116, seed=13, mood=mood)
            self.assertEqual(a.ndim, 2)
            self.assertEqual(a.shape[1], 2)
            self.assertEqual(a.dtype, np.float32)
            self.assertTrue(np.array_equal(a, b), f"Mood {mood} không tất định")
            self.assertLessEqual(float(np.abs(a).max()), 0.98)
            # Dead-air drop check: energy ~0.18s before stop_at must be dramatically quieter than body
            body_rms = float(np.sqrt(np.mean(a[int(1.0 * musicgen.SR) : int(3.5 * musicgen.SR)] ** 2)))
            gap_rms = float(np.sqrt(np.mean(a[int(4.25 * musicgen.SR) : int(4.45 * musicgen.SR)] ** 2)))
            self.assertGreater(body_rms, 0.01, f"Mood {mood} quá nhỏ")
            self.assertLess(gap_rms, body_rms * 0.15, f"Mood {mood} thiếu dramatic dead-air drop trước stop_at")
            rendered[mood] = a

        # Pairwise distinct waveforms
        for i, m1 in enumerate(expected_moods):
            for m2 in expected_moods[i + 1 :]:
                diff = float(np.mean(np.abs(rendered[m1] - rendered[m2])))
                self.assertGreater(diff, 0.01, f"Mood {m1} và {m2} quá giống nhau")

    def test_wp4_six_agency_sfx_clean_no_clip(self):
        new_sfx = ("sub_drop", "riser_long", "tape_stop", "paper_rustle", "neural_pulse", "swish_match")
        for name in new_sfx:
            self.assertIn(name, sfx.DESCRIPTIONS, f"Thiếu SFX '{name}' trong DESCRIPTIONS")
            wave = sfx._make(name)
            self.assertGreater(len(wave), 1000, f"SFX '{name}' quá ngắn")
            peak = float(np.abs(wave).max())
            self.assertGreater(peak, 0.2, f"SFX '{name}' gần như im lặng")
            self.assertLessEqual(peak, 0.98, f"SFX '{name}' bị clip (peak={peak})")

    # ---- WP-5: 6 Director Archetypes, Rotation & Viral Brief ----
    def test_wp5_archetypes_rotation_and_brief(self):
        with open(os.path.join(CONFIG_DIR, "archetypes.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        archs = cfg.get("archetypes") or {}
        self.assertEqual(len(archs), 6)
        for aid in (
            "visceral_anatomy",
            "forensic_dossier",
            "editorial_clash",
            "ticking_clock",
            "myth_autopsy",
            "one_object_odyssey",
        ):
            self.assertIn(aid, archs)

        # Rotation without repeats across 6 consecutive topics
        picked = []
        topics = [
            "Inside your heart during a marathon",
            "The unexplained carb rinse lab study",
            "Zone 2 vs HIIT efficiency race",
            "Minute by minute core heat countdown",
            "The lactic acid myth is wrong",
            "Follow a single drop of sweat",
        ]
        for idx, topic in enumerate(topics):
            recent_window = list(reversed(picked[-4:]))
            with mock.patch.object(narratives, "recent_archetypes", return_value=recent_window):
                res = narratives.plan_archetype(topic, slug=f"test-topic-{idx}")
            aid = res["archetype"]
            if picked:
                self.assertNotEqual(aid, picked[-1], f"Lặp archetype liên tiếp ở topic {idx}")
            self.assertNotIn(aid, recent_window, f"Lặp archetype trong cửa sổ avoid_recent ở topic {idx}")
            picked.append(aid)

        txt = brief.build(
            "Why heat stops runners first",
            "why-heat-stops-runners",
            plan={"style": "vox-editorial-black", "uses_flow": False, "archetype": "ticking_clock"},
        )
        self.assertIn("DIRECTOR ARCHETYPE FOR THIS VIDEO", txt)
        self.assertIn("ticking_clock", txt)
        self.assertIn("But / Therefore", txt)
        self.assertIn("dossier", txt)
        self.assertIn("xray_cutaway", txt)
        self.assertIn("hero_stat", txt)
        self.assertIn("story_hud", txt)

    # ---- WP-6: Viral Scorecard, Motionplan, Linter & QAReport ----
    def test_wp6_viralscore_separates_powerpoint_vs_agency(self):
        boring = viralscore.score_storyboard(_boring_powerpoint_sb())
        agency = viralscore.score_storyboard(_agency_viral_sb())
        self.assertLess(boring["total"], 60, f"Storyboard PowerPoint nhạt phải < 60 (got {boring})")
        self.assertEqual(boring["grade"], "D")
        self.assertGreaterEqual(agency["total"], 85, f"Storyboard Agency Vòng 13 phải ≥ 85 (got {agency})")
        self.assertIn(agency["grade"], ("A", "S"))
        self.assertEqual(sum(agency["max_axes"].values()), 100)
        self.assertEqual(set(agency["axes"]), set(viralscore.MAX_AXES))

    def test_wp6_motionplan_and_linter_support_r13_beats(self):
        ms = set(motionplan.cfg()["mechanism_scenes"])
        for beat in ("dossier", "xray_cutaway", "hero_stat"):
            self.assertIn(beat, ms)
        self.assertEqual(motionplan.check_library(), [])

        # Clean R13 cinema beats pass clutter linter; overloaded dossier fails
        agency_sb = _agency_viral_sb()
        self.assertEqual(linter.lint_clutter(agency_sb), [])
        overloaded = {
            "shots": [
                {
                    "id": "C02",
                    "beat": "setup",
                    "code": {
                        "engine": "html",
                        "scene": "dossier",
                        "params": {
                            "headline": "Short headline",
                            "evidence": [{"k": f"K{i}", "v": f"V{i}"} for i in range(6)],
                        },
                    },
                }
            ]
        }
        self.assertTrue(any(i["where"] == "C02" for i in linter.lint_clutter(overloaded)))

        # Linter emits viral warning only when archetype is set and score < min_score
        weak_with_arch = _boring_powerpoint_sb()
        weak_with_arch["archetype"] = "forensic_dossier"
        viral_issues = linter.lint_viral(weak_with_arch)
        self.assertEqual(len(viral_issues), 1)
        self.assertEqual(viral_issues[0]["where"], "viral")
        self.assertEqual(linter.lint_viral(_boring_powerpoint_sb()), [])
        self.assertEqual(linter.lint_viral(agency_sb), [])

    def test_wp6_qareport_renders_viral_scorecard(self):
        sb = _agency_viral_sb()
        ctx = {
            "title": sb["title"],
            "style": sb["style"],
            "duration": 21.0,
            "n_shots": len(sb["shots"]),
            "outro_sec": 0.0,
            "avg_shot": 3.0,
            "kinds": {"code3d": len(sb["shots"])},
            "auto_punches": 0,
            "checks": {"kích thước": ("1080x1920", True)},
            "ingest": {},
            "trims": {},
            "cuts": [],
            "text_events": [],
            "mix": {"vo": True, "music": "synth", "sfx": [], "levels": {"mode": "rms"}},
            "sb": sb,
        }
        with tempfile.TemporaryDirectory() as tmp:
            qa_dir = os.path.join(tmp, "qa")
            os.makedirs(qa_dir, exist_ok=True)
            md_path = os.path.join(qa_dir, "report.md")
            html_path = os.path.join(qa_dir, "report.html")
            qareport.write_report(md_path, ctx)
            qareport.write_html(html_path, ctx, tmp)
            with open(md_path, encoding="utf-8") as fh:
                md_txt = fh.read()
            with open(html_path, encoding="utf-8") as fh:
                html_txt = fh.read()
            self.assertIn("## Điểm Viral & Craft (Agency Scorecard)", md_txt)
            self.assertIn("forensic_dossier", md_txt)
            self.assertIn("hook_loop", md_txt)
            self.assertIn("Điểm Viral &amp; Craft (Agency Scorecard)", html_txt)
            self.assertIn("forensic_dossier", html_txt)


if __name__ == "__main__":
    unittest.main()
