import unittest

from tests.helpers import demo, mini, snapshot
from vidlib import compiler

OMNI = {"durations_sec": list(range(3, 16)), "preferred_max_sec": 10, "frames": "first_last",
        "first_last_max_sec": 10, "ingredients_max": 3, "timestamp_style": "omni"}
VEO = {"durations_sec": [4, 6, 8], "frames": "first_last", "ingredients_max": 0, "timestamp_style": "veo"}
FIRST_ONLY = {"durations_sec": [4, 6, 8], "frames": "first", "ingredients_max": 3}


class ModeRules(unittest.TestCase):
    def mode(self, caps, **over):
        return compiler.choose_mode(mini(**over)["shots"][0], caps)[0]

    def test_default_is_frames_start(self):
        self.assertEqual(self.mode(OMNI), "frames_start")

    def test_state_change_uses_start_end(self):
        self.assertEqual(self.mode(OMNI, state_change=True), "frames_start_end")

    def test_state_change_falls_back_without_last_frame(self):
        self.assertEqual(self.mode(FIRST_ONLY, state_change=True), "frames_start")

    def test_continuation_uses_seed(self):
        sb = mini()
        s2 = dict(sb["shots"][0], id="C02", continues_from="C01")
        from vidlib import storyboard
        sb = storyboard.normalize({"topic": "t", "shots": [sb["shots"][0], s2]})
        mode, why = compiler.choose_mode(sb["shots"][1], OMNI)
        self.assertEqual(mode, "frames_start")
        self.assertEqual(sb["shots"][1]["start_frame"]["seed_from"], "C01")
        self.assertIn("C01", why)

    def test_ingredients_when_free_layout(self):
        self.assertEqual(self.mode(OMNI, refs=["REF_A"], layout_free=True), "ingredients")

    def test_ingredients_needs_capacity(self):
        self.assertEqual(self.mode(VEO, refs=["REF_A"], layout_free=True), "frames_start")
        self.assertEqual(self.mode(dict(OMNI, ingredients_max=1), refs=["REF_A", "REF_B"], layout_free=True),
                         "frames_start")

    def test_explicit_unsupported_mode_falls_back(self):
        self.assertEqual(self.mode(FIRST_ONLY, mode="frames_start_end"), "frames_start")

    def test_never_text_to_video(self):
        for caps in (OMNI, VEO, FIRST_ONLY):
            for over in ({}, {"state_change": True}, {"refs": ["REF_A"], "layout_free": True}):
                self.assertIn(self.mode(caps, **over), ("frames_start", "frames_start_end", "ingredients"))


class GenSeconds(unittest.TestCase):
    def test_round_up_to_model_duration(self):
        s = mini(target_sec=1.4, trim={"speed": 1.15})["shots"][0]
        self.assertEqual(compiler.gen_seconds(s, OMNI, 1.5), 4)  # 1.4×1.15+1.5 = 3.11 → 4
        self.assertEqual(compiler.gen_seconds(s, VEO, 1.5), 4)
        s = mini(target_sec=3.0)["shots"][0]
        self.assertEqual(compiler.gen_seconds(s, VEO, 1.5), 6)   # 4.5 → 6

    def test_first_last_capped(self):
        s = mini(target_sec=3.5, trim={"speed": 1.35})["shots"][0]
        caps = dict(OMNI, first_last_max_sec=5)
        self.assertLessEqual(compiler.gen_seconds(s, caps, 1.5, mode="frames_start_end"), 5)

    def test_prefers_cheap_durations(self):
        s = mini(target_sec=3.0)["shots"][0]
        self.assertLessEqual(compiler.gen_seconds(s, OMNI, 1.5), 10)


class Prompts(unittest.TestCase):
    def test_timestamp_styles(self):
        self.assertEqual(compiler.timestamp(0, 1.5, "omni"), "[0-1.5s]")
        self.assertEqual(compiler.timestamp(0, 2, "veo"), "[00:00-00:02]")

    def test_video_prompt_has_all_blocks_in_order(self):
        sb = compiler.compile_all(demo())
        vp = sb["shots"][0]["video_prompt"]
        order = [vp.index(k) for k in ("Single continuous shot", "[0-", "provided start frame", "Motion starts",
                                       "Flat 2D vector animation, matches", "Audio: complete silence", "Avoid:")]
        self.assertEqual(order, sorted(order))

    def test_start_end_mentions_end_frame(self):
        sb = compiler.compile_all(demo())
        c10 = next(s for s in sb["shots"] if s["id"] == "C10")
        self.assertEqual(c10["mode_resolved"], "frames_start_end")
        self.assertIn("provided end frame", c10["video_prompt"])
        self.assertTrue(c10["end_frame"]["prompt"])

    def test_refs_go_into_image_prompt(self):
        sb = compiler.compile_all(demo())
        self.assertIn("REF_RUNNER", sb["shots"][0]["start_frame"]["prompt"])

    def test_avoid_drop(self):
        s = mini(avoid_drop=["extra characters"])["shots"][0]
        self.assertNotIn("extra characters", compiler.avoid_block(s))
        self.assertIn("watermark", compiler.avoid_block(s))

    def test_override_wins(self):
        sb = compiler.compile_all(mini(override={"video_prompt": "custom"}))
        self.assertEqual(sb["shots"][0]["video_prompt"], "custom")

    def test_mode_not_overwritten(self):
        sb = compiler.compile_all(mini(state_change=True))
        self.assertEqual(sb["shots"][0]["mode"], "auto")
        self.assertEqual(sb["shots"][0]["mode_resolved"], "frames_start_end")


class Snapshot(unittest.TestCase):
    def test_demo_snapshot(self):
        sb = compiler.compile_all(demo())
        data = {
            "shots": [{k: s[k] for k in ("id", "mode_resolved", "gen_sec", "video_prompt")} |
                      {"start": s["start_frame"]["prompt"], "end": s["end_frame"]["prompt"]} for s in sb["shots"]],
            "ingredients": [i["image_prompt"] for i in sb["ingredients"]],
            "thumbnails": [v["bg_prompt"] for v in sb["thumbnail"]["variants"]],
            "outro": sb["outro"]["bg_prompt"],
        }
        snapshot("compiler_demo", data, self)


if __name__ == "__main__":
    unittest.main()
