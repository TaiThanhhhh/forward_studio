import unittest

from tests.helpers import demo, mini
from vidlib import compiler, linter


def issues(sb, level=None):
    out = linter.lint(compiler.compile_all(sb))
    return [i for i in out if level is None or i["level"] == level]


def msgs(sb, level="error"):
    return " | ".join(i["msg"] for i in issues(sb, level))


class Linter(unittest.TestCase):
    def test_demo_has_no_errors(self):
        self.assertEqual(issues(demo(), "error"), [])

    def test_missing_blocks(self):
        m = msgs(mini(override={"video_prompt": "Single continuous shot. A ball bounces."}))
        for b in ("MOTION", "AUDIO", "AVOID", "STYLE"):
            self.assertIn(b, m)

    def test_word_limit(self):
        long_action = [{"t": [0, 2], "do": " ".join(["the white ball bounces"] * 30)}]
        self.assertIn("giới hạn", msgs(mini(action=long_action)))

    def test_frames_must_mention_start_frame(self):
        sb = mini()
        good = compiler.compile_all(sb)["shots"][0]["video_prompt"]
        sb["shots"][0]["override"] = {"video_prompt": good.replace("Starts exactly on the provided start frame.", "")}
        self.assertIn("start frame", msgs(sb))

    def test_onscreen_text_in_visuals_is_error(self):
        for bad in ('A sign reading "STOP" appears', "The scoreboard shows the result",
                    "A thermometer marked 3000 °C rises", "Big letters spell the answer"):
            sb = mini(action=[{"t": [0, 2], "do": bad}])
            self.assertIn("hậu kỳ", msgs(sb), bad)

    def test_possessives_are_not_quoted_text(self):
        sb = mini(action=[{"t": [0, 2], "do": "The thermometer's column drops and the scientist's jaw drops"}])
        self.assertNotIn("hậu kỳ", msgs(sb))
        sb = mini(action=[{"t": [0, 2], "do": "A sign shows 'DANGER' in red"}])
        self.assertIn("hậu kỳ", msgs(sb))

    def test_invalid_gen_sec(self):
        sb = compiler.compile_all(mini())
        sb["shots"][0]["gen_sec"] = 99
        self.assertTrue(any("gen_sec" in i["msg"] and i["level"] == "error" for i in linter.lint(sb)))

    def test_pacing(self):
        self.assertIn("tối đa", msgs(mini(target_sec=4.2)))
        self.assertIn("Hook", msgs(mini(target_sec=2.0), "warn"))

    def test_avoid_conflict_hint(self):
        sb = mini(action=[{"t": [0, 2], "do": "A crowd of white balls bounces together"}])
        self.assertIn("avoid_drop", msgs(sb, "warn"))
        sb = mini(action=[{"t": [0, 2], "do": "A crowd of white balls bounces together"}],
                  avoid_drop=["extra characters"])
        self.assertNotIn("avoid_drop", msgs(sb, "warn"))

    def test_too_many_refs_for_ingredients(self):
        sb = mini(refs=["REF_A", "REF_B"], layout_free=True, mode="ingredients")
        sb["ingredients"] += [{"id": f"REF_{k}", "desc": "x", "file": ""} for k in "CDE"]
        sb["shots"][0]["refs"] = ["REF_A", "REF_B", "REF_C", "REF_D"]
        cs = compiler.compile_all(sb)
        cs["shots"][0]["mode_resolved"] = "ingredients"
        self.assertTrue(any("ingredients" in i["msg"] for i in linter.lint(cs) if i["level"] == "error"))


if __name__ == "__main__":
    unittest.main()
