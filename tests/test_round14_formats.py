"""Vòng 14 — Dynamic Format Families & Format-Agnostic Viral Scorecard tests."""
import unittest
from unittest import mock

from vidlib import brief, narratives, storyboard, viralscore


def _evidence_board_sb():
    return storyboard.normalize({
        "topic": "How one line of code blew up a $370 million rocket",
        "title": "One Line of Code Blew Up a $370M Rocket",
        "style": "board-black",
        "assembly": "board_spine",
        "format_family": "evidence_board_doc",
        "archetype": "forensic_dossier",
        "narrative": "mystery",
        "shots": [
            {
                "id": "C01",
                "beat": "hook",
                "target_sec": 2.2,
                "beat_recipe": "NUMBER_CARD",
                "vo": "Thirty seven seconds after liftoff, a brand new European rocket vanished.",
                "sfx": ["sub_drop"],
                "board": {"number": "37 SEC", "caption": "JUNE 4, 1996 · FLIGHT 501", "sync": "vo_word:thirty"},
            },
            {
                "id": "C02",
                "beat": "setup",
                "target_sec": 3.0,
                "beat_recipe": "REVEAL_PHOTO",
                "mode": "code",
                "vo": "Every engine was healthy, so everyone on the ground expected orbit.",
                "sfx": ["shutter"],
                "code": {"engine": "three", "scene": "stage", "params": {"props": [{"type": "rocket"}]}},
                "board": {"fill": True, "caption": "KOUROU LAUNCH PAD"},
            },
            {
                "id": "C03",
                "beat": "setup",
                "target_sec": 3.2,
                "beat_recipe": "DOC_FOCUS",
                "vo": "Yet the inquiry found zero leaks, zero broken valves, and perfect thrust.",
                "sfx": ["paper_rustle"],
                "board": {
                    "lines": ["FLIGHT 501 REPORT", "ENGINES: NOMINAL", "PRESSURE: OK"],
                    "circle": "ENGINES: NOMINAL",
                    "sync": "vo_word:zero",
                },
            },
            {
                "id": "C04",
                "beat": "escalate",
                "target_sec": 2.6,
                "beat_recipe": "STAMP",
                "vo": "Instead, the killer was a single silent software bug.",
                "sfx": ["stamp", "riser_long"],
                "board": {"text": "SOFTWARE BUG", "sync": "vo_word:killer"},
            },
            {
                "id": "C05",
                "beat": "escalate",
                "target_sec": 3.2,
                "beat_recipe": "DOC_FOCUS",
                "vo": "Because the guidance computer shoved a sixty four bit velocity into sixteen bits.",
                "sfx": ["marker"],
                "board": {
                    "lines": ["SRI MODULE", "64-BIT TO 16-BIT", "MAX 32,767"],
                    "circle": "64-BIT TO 16-BIT",
                    "sync": "vo_word:sixty",
                },
            },
            {
                "id": "C06",
                "beat": "payoff",
                "target_sec": 3.0,
                "beat_recipe": "COUNTER",
                "vo": "The number climbed past thirty two thousand until memory overflowed.",
                "sfx": ["tick", "sting"],
                "board": {"label": "HORIZONTAL VELOCITY", "from": 28000, "to": 32767, "unit": "INT16"},
            },
            {
                "id": "C07",
                "beat": "payoff",
                "target_sec": 3.2,
                "beat_recipe": "REVEAL_PHOTO",
                "mode": "code",
                "vo": "Both computers crashed, so diagnostic junk jammed the nozzles hard over.",
                "sfx": ["boom"],
                "code": {"engine": "three", "scene": "stage", "params": {"props": [{"type": "rocket"}]}},
                "board": {"fill": True, "from": "C05", "caption": "NOZZLE HARD OVER"},
            },
            {
                "id": "C08",
                "beat": "twist",
                "target_sec": 3.4,
                "beat_recipe": "THESIS",
                "vo": "Except that code was copied from Ariane four and was never needed in flight.",
                "sfx": ["sting", "paper"],
                "board": {
                    "old": "HARDWARE FAILURE",
                    "new": "UNUSED REUSED CODE",
                    "strike_sync": "vo_word:copied",
                    "new_sync": "vo_word:never",
                    "from": "C07",
                },
            },
            {
                "id": "C09",
                "beat": "outro",
                "target_sec": 1.6,
                "beat_recipe": "NETWORK_REVEAL",
                "vo": "",
                "sfx": ["sub_drop"],
                "board": {},
            },
        ],
    })


def _cinema_3d_sb():
    return storyboard.normalize({
        "topic": "What happens if a steel ball drops from orbit",
        "title": "Steel Ball From Orbit",
        "style": "clay3d-black",
        "assembly": "cuts",
        "format_family": "cinema_3d_film",
        "archetype": "miniature_lab",
        "outro": {"mode": "loop", "bridge_frames": 8},
        "shots": [
            {
                "id": "C01",
                "beat": "hook",
                "target_sec": 2.2,
                "mode": "code",
                "vo": "Drop a tungsten sphere from orbit and watch physics erase a building.",
                "sfx": ["sub_drop"],
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {"props": [{"type": "anvil"}], "frame": {"preset": "ecu_macro"}, "fx": "sparks"},
                },
            },
            {
                "id": "C02",
                "beat": "setup",
                "target_sec": 3.0,
                "mode": "code",
                "transition_in": "whip_match",
                "vo": "At first, thin air barely slows it, yet friction heats the nose white hot.",
                "sfx": ["riser_long"],
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {"props": [{"type": "anvil"}], "frame": {"preset": "tracking_low"}, "fx": "fire"},
                },
            },
            {
                "id": "C03",
                "beat": "escalate",
                "target_sec": 3.2,
                "mode": "code",
                "transition_in": "iris_match",
                "vo": "Because kinetic energy scales with speed squared, air becomes solid concrete.",
                "sfx": ["neural_pulse"],
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {"props": [{"type": "anvil"}], "frame": {"preset": "low_hero"}, "fx": "smoke"},
                },
            },
            {
                "id": "C04",
                "beat": "payoff",
                "target_sec": 3.0,
                "mode": "code",
                "transition_in": "tape_stop",
                "vo": "Instead of melting away, the dense core punches straight into bedrock.",
                "sfx": ["boom"],
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {"props": [{"type": "anvil"}], "frame": {"preset": "dolly_zoom"}, "fx": "explosion"},
                },
            },
            {
                "id": "C05",
                "beat": "twist",
                "target_sec": 2.8,
                "mode": "code",
                "transition_in": "whip_match",
                "vo": "Zero explosives needed, which is why engineers fear what happens when you...",
                "sfx": ["sting"],
                "code": {
                    "engine": "three",
                    "scene": "stage",
                    "params": {"props": [{"type": "anvil"}], "frame": {"preset": "over_shoulder"}, "mood": "dark"},
                },
            },
        ],
    })


def _boring_ppt_sb():
    return storyboard.normalize({
        "topic": "Generic slideshow",
        "style": "hud-black",
        "shots": [
            {
                "id": f"C0{i + 1}",
                "beat": "hook" if i == 0 else "escalate",
                "target_sec": 3.2 if i == 0 else 2.5,
                "mode": "code",
                "vo": "Today we will learn an interesting science fact for you." if i == 0 else "Next thing happens.",
                "code": {"engine": "html", "scene": "fact", "params": {"text": f"Point {i + 1}"}},
            }
            for i in range(5)
        ],
    })


class Round14FormatFamiliesTests(unittest.TestCase):
    def test_formats_config_has_five_distinct_families(self):
        cfg = narratives.formats_config()
        self.assertEqual(cfg.get("avoid_recent"), 3)
        fids = narratives.format_ids()
        self.assertEqual(
            set(fids),
            {
                "evidence_board_doc",
                "cinema_3d_film",
                "editorial_infographic",
                "infinite_zoom_journey",
                "fast_tech_autopsy",
                "illustrated_2d_explainer",
            },
        )
        for fid in fids:
            d = narratives.get_format(fid)
            for k in ("name", "assembly", "styles", "pov", "visual_grammar", "forbidden_habits"):
                self.assertTrue(d.get(k), f"{fid} missing {k}")

    def test_plan_format_matches_topic_and_avoids_recent(self):
        with mock.patch.object(narratives, "recent_formats", return_value=[]):
            pl = narratives.plan_format("How one software bug blew up a 1996 rocket disaster", slug="ariane-5")
            self.assertEqual(pl["format_family"], "evidence_board_doc")
        with mock.patch.object(
            narratives, "recent_formats", return_value=["editorial_infographic", "evidence_board_doc", "fast_tech_autopsy"]
        ):
            pl2 = narratives.plan_format("What happens to your muscles", slug="muscle-test")
            self.assertNotIn(pl2["format_family"], {"editorial_infographic", "evidence_board_doc", "fast_tech_autopsy"})

    def test_brief_renders_format_block(self):
        b = brief.build(
            "Ariane 5 rocket bug",
            "ariane-5-test",
            plan={"style": "board-black", "uses_flow": False, "format_family": "evidence_board_doc"},
        )
        self.assertIn("FORMAT FAMILY FOR THIS VIDEO", b)
        self.assertIn("evidence_board_doc", b)
        self.assertIn("board_spine", b)

    def test_storyboard_validate_format_family(self):
        sb = _evidence_board_sb()
        errs, warns = storyboard.validate(sb)
        self.assertEqual(errs, [], f"unexpected errors: {errs}")
        self.assertFalse(any("format_family" in w for w in warns))

        sb["format_family"] = "unknown_fmt"
        errs2, warns2 = storyboard.validate(sb)
        self.assertEqual(errs2, [])
        self.assertTrue(any("format_family" in w for w in warns2))

        sb["format_family"] = 123
        errs3, _ = storyboard.validate(sb)
        self.assertTrue(any("format_family" in e for e in errs3))

    def test_viralscore_format_agnostic_evidence_board_scores_s(self):
        sb = _evidence_board_sb()
        res = viralscore.score_storyboard(sb)
        self.assertEqual(res["format_family"], "evidence_board_doc")
        self.assertGreaterEqual(res["total"], 90, f"Board doc scored {res['total']} ({res['axes']}): {res['suggestions']}")
        self.assertEqual(res["grade"], "S")

    def test_viralscore_format_agnostic_cinema_3d_scores_high(self):
        sb = _cinema_3d_sb()
        res = viralscore.score_storyboard(sb)
        self.assertEqual(res["format_family"], "cinema_3d_film")
        self.assertGreaterEqual(res["total"], 88, f"3D film scored {res['total']} ({res['axes']}): {res['suggestions']}")
        self.assertIn(res["grade"], ("S", "A"))

    def test_viralscore_boring_powerpoint_still_fails(self):
        res = viralscore.score_storyboard(_boring_ppt_sb())
        self.assertEqual(res["format_family"], "editorial_infographic")
        self.assertLess(res["total"], 60)
        self.assertEqual(res["grade"], "D")

    def test_viralscore_penalizes_consecutive_same_format(self):
        sb = _cinema_3d_sb()
        base = viralscore.score_storyboard(sb)
        rep = viralscore.score_storyboard(sb, history=[{"format_family": "cinema_3d_film"}])
        self.assertLess(rep["axes"]["narrative_freshness"], base["axes"]["narrative_freshness"])


if __name__ == "__main__":
    unittest.main()
