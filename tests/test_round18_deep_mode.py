"""Vòng 18 (PR-16): kiểm tra chế độ Mini Deep-Dive 65–90s (--length deep), chunked TTS & Gemini 503 fallback."""
import os
import sys
import types
import unittest
from unittest import mock

from vidlib import brief, linter, storyboard, tts, viralscore
from vidlib.common import duration_profile


def _deep_storyboard():
    shots = []
    vo_lines = [
        ("hook", 2.2, "One missing check crashed a three hundred million dollar rocket in thirty seven seconds."),
        ("setup", 3.8, "Engineers reused navigation code from an older rocket without testing the new thrust curve."),
        ("escalate", 4.0, "Because the new booster accelerated five times faster, a tiny sensor number spiked."),
        ("escalate", 3.8, "Inside the flight computer, that sideways velocity had to fit inside sixteen bits."),
        ("escalate", 4.0, "Yet the number climbed past thirty two thousand seven hundred sixty seven and overflowed."),
        ("escalate", 3.8, "Instead of ignoring the error, the backup computer crashed on the exact same line."),
        ("escalate", 4.0, "Here is the twist nobody expected: the main computer treated diagnostic text as flight data."),
        ("escalate", 4.0, "So it commanded the main nozzles to swivel hard over to correct a phantom tilt."),
        ("escalate", 3.8, "Aerodynamic forces ripped the boosters clean off the core stage within two seconds."),
        ("escalate", 4.0, "Automatic self destruct charges fired immediately to protect the launch site below."),
        ("escalate", 4.0, "But why was that calibration routine even running after liftoff in the first place?"),
        ("escalate", 3.8, "Because on the older rocket it saved forty seconds during a launch hold."),
        ("escalate", 4.0, "Yet on the new rocket that routine served zero purpose once the engines ignited."),
        ("escalate", 3.8, "Engineers left it active because removing working code felt riskier than keeping it."),
        ("escalate", 4.0, "And the two overflow guards were deleted earlier to save precious processor cycles."),
        ("escalate", 3.8, "Nobody simulated the real horizontal trajectory because they assumed the old math held."),
        ("payoff", 4.0, "One single integer overflow turned ten years of aerospace engineering into fireworks."),
        ("twist", 3.8, "The deadliest bug was never a typo — it was trusting yesterday's assumptions today."),
        ("outro", 1.4, ""),
    ]
    recipes = ["NUMBER_CARD", "DOC_FOCUS", "COUNTER", "DOC_FOCUS", "NUMBER_CARD", "STAMP"]
    for idx, (beat, sec, vo) in enumerate(vo_lines, start=1):
        rec = "NETWORK_REVEAL" if beat == "outro" else ("THESIS" if beat == "twist" else recipes[(idx - 1) % len(recipes)])
        board = {}
        if rec == "NUMBER_CARD":
            board = {"number": "32,767", "from": 0, "caption": "MAX 16-BIT"}
        elif rec == "DOC_FOCUS":
            board = {"lines": ["FLIGHT LOG", "Overflow at 37s"], "circle": "Overflow"}
        elif rec == "COUNTER":
            board = {"label": "VELOCITY", "from": 0, "to": 32768, "unit": "bit", "decimals": 0}
        elif rec == "STAMP":
            board = {"text": "CONFIRMED"}
        elif rec == "THESIS":
            board = {"old": "A simple typo", "new": "Yesterday's assumption"}
        shots.append({
            "id": f"C{idx:02d}",
            "beat": beat,
            "target_sec": sec,
            "vo": vo,
            "mode": "code",
            "beat_recipe": rec,
            "board": board,
            "transition_in": "iris_match" if idx in (7, 11) else "cut",
            "sfx": ["boom" if idx == 1 else ("riser" if idx in (6, 10) else "paper")],
        })
    sb = {
        "slug": "deep-dive-demo",
        "topic": "Why one integer overflow blew up a rocket",
        "title": "Why One Integer Overflow Blew Up a Rocket",
        "language": "en",
        "style": "board-black",
        "assembly": "board_spine",
        "format_family": "evidence_board_doc",
        "archetype": "forensic_mystery",
        "length_profile": "deep",
        "format": {"aspect": "9:16", "fps": 30, "target_sec": 75},
        "outro": {"mode": "loop", "bridge_frames": 8},
        "shots": shots,
    }
    return storyboard.normalize(sb)


class TestRound18DeepMode(unittest.TestCase):
    def test_duration_profile_resolves_short_and_deep(self):
        short_p = duration_profile("short")
        deep_p = duration_profile("deep")
        self.assertEqual(short_p["name"], "short")
        self.assertEqual(short_p["max_sec"], 45)
        self.assertEqual(deep_p["name"], "deep")
        self.assertGreaterEqual(deep_p["min_sec"], 60)
        self.assertEqual(deep_p["target_sec"], 75)
        self.assertEqual(deep_p["board_maxrate"], "6M")

        # Auto-detection from storyboard format.target_sec >= 60
        inferred = duration_profile({"format": {"target_sec": 72}})
        self.assertEqual(inferred["name"], "deep")

    def test_brief_build_injects_deep_dive_instructions(self):
        txt = brief.build("Why quantum computers break RSA", "quantum-rsa", plan={"length_profile": "deep"})
        self.assertIn("62–95s, target about 75s", txt)
        self.assertIn("MINI DEEP-DIVE MODE", txt)
        self.assertIn("TikTok Creator Rewards", txt)

    def test_linter_and_viralscore_accept_75s_deep_storyboard(self):
        sb = _deep_storyboard()
        issues = linter.lint_pacing(sb)
        dur_warns = [x for x in issues if "ngoài khoảng" in x["msg"] or "dài hơn" in x["msg"] or "ngắn hơn" in x["msg"]]
        self.assertEqual(dur_warns, [])

        vs = viralscore.score_storyboard(sb)
        self.assertGreaterEqual(vs["axes"]["retention_pacing"], 7)
        self.assertGreaterEqual(vs["total"], 85)

    def test_tts_split_chunks_splits_only_long_scripts(self):
        short_lines = [{"text": "Short hook sentence here.", "beat": "hook"} for _ in range(5)]
        self.assertEqual(len(tts._split_chunks(short_lines)), 1)

        long_lines = [
            {
                "text": f"Sentence number {i} explains a concrete physical mechanism in clear spoken English.",
                "beat": "escalate",
            }
            for i in range(30)
        ]
        chunks = tts._split_chunks(long_lines, max_chars=700)
        self.assertGreater(len(chunks), 2)
        reconstructed = sum(len(sub) for _, sub in chunks)
        self.assertEqual(reconstructed, len(long_lines))

    def test_brief_ask_gemini_falls_back_on_503(self):
        seen_models = []

        class _Interactions:
            def create(self, **kwargs):
                seen_models.append(kwargs["model"])
                if kwargs["model"] == "gemini-4-hydrogen":
                    raise RuntimeError("Error code: 503 - service_unavailable high demand")
                return types.SimpleNamespace(
                    output_text='{"ok": true}',
                    usage=types.SimpleNamespace(total_input_tokens=10, total_output_tokens=5),
                )

        class _Client:
            def __init__(self, api_key=None, http_options=None):
                self.interactions = _Interactions()

        google_mod = types.ModuleType("google")
        genai_mod = types.ModuleType("google.genai")
        genai_mod.Client = _Client
        google_mod.genai = genai_mod

        with (
            mock.patch.dict(sys.modules, {"google": google_mod, "google.genai": genai_mod}),
            mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k", "GEMINI_TEXT_MODEL": ""}, clear=False),
        ):
            out = brief.ask("gemini", "Return JSON")
        self.assertEqual(out, '{"ok": true}')
        self.assertEqual(seen_models, ["gemini-4-hydrogen", "gemini-3.8-flash"])


if __name__ == "__main__":
    unittest.main()
