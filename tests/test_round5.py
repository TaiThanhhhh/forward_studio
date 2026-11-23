"""Vòng 5: mix khoá mức (gated RMS), camera ảo không lộ mép + không đứng hình, chọn style chống lặp, tự chọn mode code,
linter script tiếng Anh, ideas, publish."""
import os
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw

from vidlib import codeshot, compiler, ideas, linter, mix, qareport, storyboard, styles, vcam
from vidlib.common import H, W, db2amp


def _tone(sec, f, sr=48000, amp=0.3, gaps=False):
    t = np.arange(int(sec * sr)) / sr
    a = amp * np.sin(2 * np.pi * f * t)
    if gaps:  # có khoảng lặng như lời nói
        a *= (np.sin(2 * np.pi * 0.7 * t) > -0.2)
    return np.stack([a, a], 1).astype(np.float32)


class MixLock(unittest.TestCase):
    def test_music_and_sfx_locked_to_voice(self):
        sr = 48000
        voice = _tone(6, 220, amp=0.4, gaps=True)
        music = _tone(6, 110, amp=0.9)
        sfx = np.zeros_like(voice)
        sfx[sr:sr + 4000] = 0.95
        out, rep = mix.lock(voice, music, sfx, sr, mode="ratio")
        self.assertAlmostEqual(rep["music_db_vs_voice"], -6.0, delta=0.3)       # nhạc = −6 dB so với giọng (gated RMS)
        self.assertLessEqual(rep["sfx_peak_vs_voice_peak"], 0.7 + 1e-3)          # đỉnh SFX ≤ 0.7× đỉnh giọng
        self.assertNotIn("ducking_db", rep)                                      # ratio = không duck
        _, rep2 = mix.lock(voice, music, sfx, sr, mode="ducking")
        self.assertEqual(rep2["ducking_db"], mix.cfg()["ducking"]["duck_db"])

    def test_gated_rms_ignores_silence(self):
        sr = 48000
        a = _tone(2, 300, amp=0.5)
        b = np.concatenate([a, np.zeros_like(a), np.zeros_like(a)])
        self.assertAlmostEqual(mix.gated_rms(a, sr), mix.gated_rms(b, sr), places=3)

    def test_master_filter_is_linear_gain_plus_limiter(self):
        f = mix.master_filter(3.5)
        self.assertIn("volume=3.500dB", f)
        self.assertIn("alimiter", f)
        self.assertNotIn("loudnorm", f)
        m = mix.cfg()["master"]                                   # trần = true_peak_db − limiter_margin_db (AUD-401: −1.5)
        self.assertLessEqual(m["true_peak_db"], -1.5)
        self.assertAlmostEqual(db2amp(m["true_peak_db"] - m["limiter_margin_db"]),
                               float(f.split("limit=")[1].split(":")[0]), places=3)


class VirtualCamera(unittest.TestCase):
    def test_min_scale_covers_roll(self):
        self.assertAlmostEqual(vcam.min_scale(0), 1.0)
        self.assertGreater(vcam.min_scale(2.0), 1.06)
        self.assertLess(vcam.min_scale(2.0), 1.12)

    def test_no_edges_and_never_static(self):
        seg = {"sid": "C01", "index": 0, "start_f": 0, "n": 60, "dur": 2.0, "zoom_base": 1.0, "punches": [(1.0, 1.08)]}
        cam = vcam.ShotCam(seg, kicks=[0.5], carry=(6.0, 0.0), payoff=True)
        img = Image.new("RGB", (W, H), (255, 255, 255))
        ImageDraw.Draw(img).ellipse([300, 600, 700, 1000], fill=(30, 30, 30))
        prev = None
        for i in range(seg["n"]):
            s, dx, dy, roll = cam.frame(i)
            self.assertLessEqual(s, vcam.cfg()["max_scale"] + 1e-6)              # ≤ 112%
            self.assertGreaterEqual(s, vcam.min_scale(roll, dx, dy) - 1e-6)      # không lộ mép
            if i % 15 == 0:
                out = np.asarray(vcam.apply(img, s, dx, dy, roll))
                self.assertTrue((out[[0, -1]].min() > 200) and (out[:, [0, -1]].min() > 200), f"lộ mép đen ở frame {i}")
            if prev is not None:
                self.assertNotEqual(prev, (s, dx, dy, roll))                     # creep: không frame nào đứng yên
            prev = (s, dx, dy, roll)

    def test_kicks_from_hit_sfx(self):
        tl = {"segments": [{"sid": "C01", "index": 0, "start_f": 0, "n": 60, "dur": 2.0, "transition": "cut"}]}
        sb = {"shots": [{"id": "C01", "beat": "payoff"}]}
        cams = vcam.plan(tl, sb, [(0.8, "hit"), (1.2, "pop")])
        self.assertEqual([k["f"] for k in cams["C01"].kicks], [24])             # chỉ SFX va chạm mới có kick


class StylesAndCode(unittest.TestCase):
    def test_toon3d_lab_registered_and_code_only(self):
        self.assertIn("toon3d-lab", styles.available())
        self.assertTrue(styles.info("toon3d-lab")["code_only"])
        self.assertIn("world", __import__("vidlib.textstyle", fromlist=["x"]).load_style("toon3d-lab"))

    def test_auto_style_avoids_recent(self):
        rec = styles.recent()
        pick, note = styles.resolve({"style": "auto"}, "__none__")
        if len(set(rec)) < len(styles.available()):
            self.assertNotIn(pick, rec)

    def test_auto_code_for_thermometer(self):
        sb = storyboard.normalize({"topic": "t", "shots": [
            {"id": "C01", "subject": "a thermometer in the glass", "start_frame": {"desc": "a thermometer"}, "action": "x"},
            {"id": "C02", "subject": "a runner", "start_frame": {"desc": "a runner"}, "action": "x"}]})
        c = compiler.compile_all(sb, auto_code_ids=["C01", "C02"])
        self.assertEqual(c["shots"][0]["mode_resolved"], "code")
        self.assertEqual(c["shots"][0]["code"]["scene"], "thermometer")
        self.assertNotEqual(c["shots"][1]["mode_resolved"], "code")
        c2 = compiler.compile_all(sb, auto_code_ids=[])                            # đã có clip Flow → giữ Flow
        self.assertNotEqual(c2["shots"][0]["mode_resolved"], "code")

    def test_engine_scenes_exist(self):
        self.assertTrue({"scale", "thermometer", "outro", "charsheet", "vacuum", "stage"} <= set(codeshot.scenes()))

    def test_brief_documents_general_stage_scene(self):
        from vidlib import brief
        t = brief.build("What happens if you put a balloon in liquid nitrogen?", "balloon")
        self.assertIn("GENERAL code scene for ANY idea", t)
        self.assertIn("props[]", t)                      # LLM tự ghép shot code cho ý tưởng mới, không cần viết JS
        self.assertNotIn("{scene_help}", t)


class EnglishScriptLint(unittest.TestCase):
    def test_digits_and_contractions(self):
        sb = storyboard.normalize({"topic": "t", "shots": [
            {"id": "C01", "beat": "hook", "vo": "It is 1,000°C and it does not touch the water at all.", "target_sec": 3,
             "start_frame": "a", "action": "b"},
            {"id": "C02", "beat": "twist", "vo": "So the glass stays at zero until the last cube melts.", "target_sec": 3,
             "start_frame": "a", "action": "b"}]})
        msgs = " ".join(i["msg"] for i in linter.lint_script(sb))
        self.assertIn("viết bằng chữ", msgs)
        self.assertIn("rút gọn", msgs)


class IdeasAndPublish(unittest.TestCase):
    def test_ideas_validate_and_autopick(self):
        good = {"title": "The Ball That Water Refuses To Touch", "hook": "Water won't touch a glowing ball.",
                "twist": "The glass stays at zero.", "visual": ["steam", "boil"], "truth": "True", "score": 7}
        data = {"ideas": [dict(good, score=k) for k in range(10)]}
        self.assertEqual(ideas.validate(data), [])
        self.assertEqual(ideas.best(data["ideas"]), 9)
        bad = {"ideas": [dict(good, truth="Maybe", hook="Is it real?")] * 10}
        errs = ideas.validate(bad)
        self.assertTrue(any("truth" in e for e in errs) and any("hook" in e for e in errs))

    def test_publish_limits(self):
        with tempfile.TemporaryDirectory() as d:
            p, warns = qareport.write_publish({"publish": {"titles": ["x" * 70], "description": "One. Two. Three.",
                                                           "hashtags": ["a"]}}, os.path.join(d, "publish.md"))
            self.assertTrue(os.path.exists(p))
            self.assertEqual(len(warns), 4)  # > 60 ký tự, < 3 tiêu đề, ≠ 2 câu, < 5 hashtag


class StyleAndLanguage(unittest.TestCase):
    def test_style_changes_flow_medium_forward_unchanged(self):
        sb = storyboard.normalize({"topic": "t", "shots": [{"id": "C01", "start_frame": {"desc": "A glass."},
                                                              "action": "It shakes."}]})
        base = compiler.compile_all(dict(sb, style_resolved="forward"))["shots"][0]["start_frame"]["prompt"]
        chalk = compiler.compile_all(dict(sb, style_resolved="chalk"))["shots"][0]["start_frame"]["prompt"]
        self.assertIn("Flat 2D vector", base)
        self.assertIn("chalk", chalk.lower())
        self.assertNotIn("Flat 2D vector", chalk)
        self.assertIn("Pure solid black background", chalk)          # nền đen giữ nguyên

    def test_old_vietnamese_project_detected(self):
        from vidlib import lang
        sb = storyboard.normalize({"topic": "t", "shots": [{"vo": "Điều gì xảy ra nếu thả viên bi vào nước đá?"}]})
        self.assertEqual(sb["language"], "vi")
        lang.set_project_language("vi")
        try:
            self.assertEqual(lang.fmt_number(1000), "1.000")
            self.assertEqual(lang.ocr_lang(), "vie+eng")
        finally:
            lang.set_project_language(None)
        self.assertEqual(lang.fmt_number(1000), "1,000")


if __name__ == "__main__":
    unittest.main()
