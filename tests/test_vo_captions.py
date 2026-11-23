"""Lời đọc tiếng Anh (căn từ, cắt lặng) + timeline cắt sớm 0–3 frame + .srt + nhịp + quy tắc số → chữ."""
import os
import tempfile
import unittest

from vidlib import fakes, lang, qa, storyboard, timeline, timing, tts, vo
from vidlib.common import FPS, channel, num_syllables, spoken_syllables

LINES = ["A steel ball at one thousand degrees won't touch the water.", "Steam wraps the ball in a soft cushion.",
         "Then the cushion collapses all at once.", "The water boils like crazy around it."]


def _sb():
    shots = []
    for i, ln in enumerate(LINES):
        shots.append({"vo": ln, "beat": ["hook", "setup", "escalate", "payoff"][i], "target_sec": 2.0,
                      "start_frame": "a", "action": "b"})
        shots.append({"vo": "", "beat": "escalate", "target_sec": 1.0, "start_frame": "a", "action": "b"})
    return storyboard.normalize({"topic": "t", "shots": shots})


class Syllables(unittest.TestCase):
    def test_vietnamese_numbers_kept(self):  # kênh tiếng Việt cũ vẫn đếm đúng
        self.assertEqual([num_syllables(n) for n in (5, 15, 21, 42, 100, 105, 2000, 2700, 50000)],
                         [1, 2, 3, 3, 2, 4, 2, 4, 3])
        self.assertEqual(spoken_syllables("42 km"), 6)

    def test_english_spoken_numbers(self):
        self.assertEqual(lang.spoken("1,000°C"), "one thousand degrees Celsius")
        self.assertEqual(lang.spoken("about 525°C"), "about five hundred twenty-five degrees Celsius")
        self.assertEqual(lang.spoken("2.5 s and 50%"), "two point five seconds and fifty percent")
        # kit cũ đếm "1,000" = 2 âm tiết; chuẩn hoá trước khi đếm → 7
        self.assertEqual(lang.syllables_spoken("1,000°C"), 7)
        self.assertEqual(lang.fmt_number(1000), "1,000")
        self.assertEqual(lang.fmt_number(1000, loc="vi-VN"), "1.000")

    def test_phrases_do_not_split_numbers(self):
        self.assertEqual(timing.phrases_of("It hit 1,000°C, then 2.5 s later, gone."),
                         ["It hit 1,000°C,", "then 2.5 s later,", "gone."])

    def test_tts_text_maps_back_to_display_words(self):
        text, words = tts.build_text([{"text": "[excited] Drop a 1,000°C ball.", "beat": "hook"},
                                      {"text": "The Leidenfrost effect.", "beat": "setup"}])
        self.assertTrue(text.startswith("[excited] Drop a one thousand degrees Celsius ball."))
        got = {w["w"]: text[w["a"]:w["b"]] for w in words}
        self.assertEqual(got["1,000°C"], "one thousand degrees Celsius")
        self.assertEqual(got["Leidenfrost"], "Lyden-frost")
        self.assertEqual(tts.strip_tags("[excited] Drop it."), "Drop it.")


class VoiceOver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.proj = cls.tmp.name
        os.makedirs(os.path.join(cls.proj, "audio"))
        cls.truth = fakes.make_vo(os.path.join(cls.proj, "audio", "vo.wav"), LINES, line_gap=0.5)
        cls.sb = _sb()
        cls.vo = vo.process(cls.proj, cls.sb, log=lambda m: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_silence_mode_is_announced(self):
        self.assertIn("khoảng lặng", self.vo["timing"])
        self.assertTrue(any("CĂN THEO KHOẢNG LẶNG" in n for n in self.vo["notes"]))

    def test_lines_found_and_ordered(self):
        self.assertEqual(len(self.vo["lines"]), len(LINES))
        starts = [ln["start"] for ln in self.vo["lines"]]
        self.assertEqual(starts, sorted(starts))
        self.assertLess(starts[0], 0.2, "VO phải bắt đầu gần frame 0 (≤ frame 6)")

    def test_silence_trimmed_and_payoff_pause(self):
        raw = self.truth[-1]["end"] + 0.5
        self.assertLess(self.vo["duration"], raw)  # lặng 0.5s giữa câu bị rút
        gaps = [b["start"] - a["end"] for a, b in zip(self.vo["lines"], self.vo["lines"][1:])]
        self.assertTrue(all(g < 0.5 for g in gaps), gaps)
        self.assertGreater(gaps[2], max(gaps[0], gaps[1]))  # trước câu payoff giữ nhịp ngừng dài hơn

    def test_line_lengths_match_truth(self):
        speed = channel()["vo"]["speed"]
        for got, want in zip(self.vo["lines"], self.truth):
            self.assertAlmostEqual(got["end"] - got["start"], (want["end"] - want["start"]) / speed, delta=0.15)

    def test_words_inside_lines(self):
        for ln in self.vo["lines"]:
            self.assertEqual(len(ln["words"]), len(ln["text"].split()))
            for w in ln["words"]:
                self.assertGreaterEqual(w["start"], ln["start"] - 0.02)
                self.assertLessEqual(w["start"], ln["end"])

    def test_cut_lands_0_to_3_frames_before_line(self):
        tl = timeline.build(self.sb, self.vo, None, 2.0)
        segs = tl["segments"]
        self.assertEqual(segs[-1]["sid"], "OUTRO")
        for ln in self.vo["lines"][1:]:
            seg = segs[ln["shots"][0]]
            lead = ln["start"] - seg["start_f"] / FPS
            self.assertGreaterEqual(lead, -0.5 / FPS)
            self.assertLessEqual(lead, 3.5 / FPS)

    def test_srt(self):
        p = os.path.join(self.proj, "out", "captions.srt")
        qa.write_srt(self.vo, p)
        with open(p, encoding="utf-8") as fh:
            txt = fh.read()
        self.assertTrue(txt.startswith("1\n00:00:00,"))
        self.assertIn("won't touch", txt)


class SplitWithCommaPauses(unittest.TestCase):
    def test_long_comma_pause_is_not_a_sentence_break(self):
        import numpy as np
        sr = 16000
        rng = np.random.default_rng(0)

        def voiced(sec):
            return rng.normal(0, 0.3, int(sec * sr)).astype(np.float32)

        def gap(sec):
            return np.zeros(int(sec * sr), np.float32)
        mono = np.concatenate([voiced(2), gap(0.6), voiced(2), gap(0.4), voiced(1), gap(0.4), voiced(3)])
        out = vo.split_lines(mono, sr, 3, 0.12, weights=[40, 10, 30])
        bounds = [round(b, 2) for _, b in out[:-1]]
        self.assertAlmostEqual(bounds[0], 4.8, delta=0.15)
        self.assertAlmostEqual(bounds[1], 6.2, delta=0.15)


class Pacing(unittest.TestCase):
    def test_change_every_rule(self):
        sb = storyboard.normalize({"topic": "t", "shots": [{"target_sec": 3.4, "start_frame": "a", "action": "b"}]})
        tl = timeline.build(sb, None, None, 0)
        seg = tl["segments"][0]
        times = [0.0] + [t for t, _ in seg["punches"]] + [seg["dur"]]
        gaps = [b - a for a, b in zip(times, times[1:])]
        self.assertLessEqual(max(gaps), channel()["pacing"]["change_every_sec"] + 1e-6)
        self.assertTrue(all(1.0 <= s <= 1.25 for _, s in seg["punches"]))

    def test_flash_guard(self):
        trans = ["cut", "flash", "flash", "flash", "flash", "flash"]
        starts = [0.0, 0.1, 0.2, 0.3, 0.4, 1.6]
        out, dropped = timeline.guard_flashes(trans, starts)
        self.assertEqual(out.count("flash"), 4)
        self.assertEqual(len(dropped), 1)

    def test_beat_snap(self):
        import numpy as np
        beats = np.arange(0, 10, 0.5)
        self.assertEqual(timeline.snap_to_beats([1.03, 2.2], beats, 2), [1.0, 2.2])


if __name__ == "__main__":
    unittest.main()
