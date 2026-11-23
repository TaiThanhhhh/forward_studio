"""Vòng 7b: mỗi video một giọng, style theo chủ đề (có hôm Flow, có hôm toàn code), đạo cụ cho mọi chủ đề.
Không gọi mạng, không render."""

import os
import tempfile
import unittest
from unittest import mock

from engines import html
from vidlib import brief, storyboard, styles, textstyle, tts, voices
from vidlib.common import StudioError


def hist(*items):
    """Giả lịch sử dự án: [(mtime, slug, giá trị)] mới nhất trước."""
    return [(100 - i, f"v{i}", x) for i, x in enumerate(items)]


class TestVoices(unittest.TestCase):
    def test_pool_is_real_and_tagged(self):
        pool = voices.pool("en", include_manual=True)
        self.assertGreaterEqual(len(pool), 15)
        self.assertEqual(len({v["id"] for v in pool}), len(pool))
        for v in pool:
            self.assertTrue(v.get("tags") and v.get("gender") and v.get("name"), v)
        self.assertTrue({"male", "female"} <= {v["gender"] for v in pool})
        manual = [v for v in pool if not v.get("auto", True)]
        self.assertTrue(manual and all("character" in v["tags"] for v in manual))
        self.assertTrue(all(v.get("auto", True) for v in voices.pool("en")))

    def test_find_by_name_or_id(self):
        b = voices.find("brian")
        self.assertEqual(b["id"], "nPczCjzI2devNBz1zQrb")
        self.assertEqual(voices.find(b["id"])["id"], b["id"])
        self.assertIsNone(voices.find("nobody"))

    def test_never_repeats_recent_voices(self):
        recent = [v["id"] for v in voices.pool("en")[:5]]
        with mock.patch.object(voices, "history", return_value=hist(*recent)):
            for style in ("hud-black", "flat-vector-black", "swiss-motion-black", "forward"):
                v, note = voices.resolve({"voice": "auto", "style_resolved": style, "language": "en"}, "new")
                self.assertNotIn(v["id"], recent, style)
                self.assertTrue(v.get("auto_pick"))
                self.assertIn("giọng auto", note)

    def test_style_shapes_voice_choice(self):
        with mock.patch.object(voices, "history", return_value=[]):
            spy = voices.ranked("spy-titles-black")[0][0]
            hud = voices.ranked("hud-black")[0][0]
        self.assertIn("storyteller", spy["tags"])
        self.assertTrue({"steady", "formal", "news", "calm"} & set(hud["tags"]))
        self.assertNotEqual(spy["id"], hud["id"])

    def test_gender_alternates_when_tags_tie(self):
        last = voices.find("Liam")
        with mock.patch.object(voices, "history", return_value=hist(last["id"])):
            v = voices.ranked("flat-vector-black")[0][0]
        self.assertNotEqual(v["gender"], "male")

    def test_stable_and_manual_override(self):
        v = {"id": "x1", "name": "Keep", "auto_pick": True}
        self.assertEqual(voices.resolve({"voice": "auto", "voice_resolved": v}, "s")[0], v)
        got, note = voices.resolve({"voice": "Daniel", "voice_resolved": v}, "s")
        self.assertEqual(voices.short(got), "Daniel")
        self.assertIsNone(note)
        bad, note = voices.resolve({"voice": "Nobody"}, "s")
        self.assertIsNone(bad)
        self.assertIn("không có giọng", note)

    def test_adaptive_tempo_and_legacy(self):
        self.assertAlmostEqual(voices.adaptive_speed(3.7), 1.0)
        self.assertAlmostEqual(voices.adaptive_speed(3.3), round(3.7 / 3.3, 3))
        self.assertEqual(voices.adaptive_speed(2.0), 1.15)  # giọng rất chậm: kẹp trần, không méo tiếng
        self.assertEqual(voices.adaptive_speed(5.0), 1.0)  # không bao giờ làm chậm lại
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "audio"))
            from vidlib.common import save_json

            save_json(os.path.join(d, "audio", "vo_alignment.json"), {"raw_words_per_sec": 3.3})
            sp, why = voices.tempo_for(d, {"voice_resolved": {"id": "a"}}, 1.12)
            self.assertAlmostEqual(sp, round(3.7 / 3.3, 3))
            self.assertIn("atempo", why)
            self.assertEqual(voices.tempo_for(d, {"voice_resolved": {"id": "a", "legacy": True}}, 1.12), (1.12, None))
            self.assertEqual(voices.tempo_for(d, {}, 1.12), (1.12, None))  # video cũ: tốc độ cố định

    def test_tts_uses_video_voice_and_cache_key_changes(self):
        cfg = tts.voice_cfg()
        text, _ = tts.build_text([{"text": "Hello there.", "beat": "setup"}], cfg)
        k1 = tts.cache_key(text, cfg)
        k2 = tts.cache_key(text, {**cfg, "voice": {"id": "nPczCjzI2devNBz1zQrb"}})
        self.assertNotEqual(k1, k2)  # đổi giọng → tạo lại giọng đọc
        seen = {}

        def fake_post(path, body, key):
            seen["path"] = path
            chars = list(body["text"])
            return {
                "audio_base64": "",
                "alignment": {
                    "characters": chars,
                    "character_start_times_seconds": [i * 0.05 for i in range(len(chars))],
                    "character_end_times_seconds": [i * 0.05 + 0.05 for i in range(len(chars))],
                },
            }

        with (
            tempfile.TemporaryDirectory() as d,
            mock.patch.object(tts, "_post", fake_post),
            mock.patch.object(tts, "env", return_value="k"),
        ):
            tts.synthesize(
                d, [{"text": "Hello there friend.", "beat": "setup"}], log=lambda m: None, voice=voices.find("Brian")
            )
        self.assertIn("nPczCjzI2devNBz1zQrb", seen["path"])


class TestStylePlan(unittest.TestCase):
    def setUp(self):
        textstyle.load_style.cache_clear()

    def test_every_style_has_topic_and_voice_tags(self):
        for sid in styles.available():
            st = textstyle.load_style(sid)
            self.assertGreaterEqual(len(st.get("tags") or []), 5, sid)
            self.assertGreaterEqual(len(st.get("voice_tags") or []), 3, sid)
            self.assertIn((st.get("html") or {}).get("look"), html.LOOKS, f"{sid}: thiếu look html cho shot motion")

    def test_topic_picks_style(self):
        with mock.patch.object(styles, "history", return_value=[]):
            cases = {
                "How big is a black hole compared to Earth?": "scale-zoom-black",
                "What happens to an astronaut in space?": "hud-black",
                "What happens if a lightning bolt hits the ocean?": "neon",
                "What if you mix baking soda and vinegar in a sealed bottle?": {"line-boil-black", "lab-notebook-black"},
            }
            for topic, want in cases.items():
                self.assertIn(styles.plan(topic)["style"], want if isinstance(want, set) else {want}, topic)

    def test_stems(self):
        self.assertGreater(styles.score("flat-vector-black", "What if you stop sleeping?"), 0)  # sleeping → sleep
        self.assertGreater(styles.score("line-boil-black", "burned and burning"), 0)

    def test_flow_and_no_flow_days(self):
        with mock.patch.object(styles, "history", return_value=[]):
            on = styles.plan("What happens if you drop a phone into lava?", flow=True)
            off = styles.plan("What happens if you drop a phone into lava?", flow=False)
        self.assertTrue(on["uses_flow"])
        self.assertFalse(off["uses_flow"])
        self.assertTrue(styles.uses_flow("forward"))
        self.assertFalse(styles.uses_flow("hud-black"))

    def test_balance_between_flow_and_code_days(self):
        topic = "What happens if you mix two random things?"  # không khớp nhãn nào → cân bằng quyết định
        with mock.patch.object(styles, "history", return_value=hist("forward", "chalk", "comic", "neon")):
            self.assertFalse(styles.plan(topic)["uses_flow"])  # 4/4 ngày Flow → hôm nay toàn code
        with mock.patch.object(styles, "history", return_value=hist("hud-black", "swiss-motion-black", "toon3d-lab")):
            self.assertTrue(styles.plan(topic)["uses_flow"])  # 3/3 ngày code → hôm nay có Flow

    def test_manual_style_and_special(self):
        self.assertEqual(styles.plan("anything", style="spy-titles-black")["reason"], "chỉ định tay (--style)")
        with self.assertRaises(StudioError):
            styles.plan("anything", style="nope")
        with mock.patch.object(styles, "history", return_value=[]):
            self.assertEqual(styles.plan("What happens if light passes through a prism into a rainbow?")["style"],
                             "gallery-pointillist-black")

    def test_brief_tells_the_writer_flow_or_not(self):
        code = brief.plan_block({"style": "hud-black", "uses_flow": False, "reason": "r", "voice": voices.find("Daniel")})
        self.assertIn("NO-FLOW DAY", code)
        self.assertIn('"style": "hud-black"', code)
        self.assertIn("Daniel", code)
        flow = brief.plan_block({"style": "forward", "uses_flow": True, "reason": "r"})
        self.assertIn("FLOW DAY", flow)
        self.assertNotIn("NO-FLOW", flow)
        board = brief.plan_block({"style": "board-black", "uses_flow": True, "reason": "r"})
        self.assertIn("evidence board", board)

    def test_old_vietnamese_projects_keep_forward(self):
        sb = storyboard.normalize(
            {"topic": "t", "shots": [{"id": "C01", "vo": "Điều gì xảy ra nếu bạn thả một viên bi sắt"}]}
        )
        self.assertEqual(sb["style"], "forward")
        sb = storyboard.normalize({"topic": "t", "language": "en", "shots": [{"id": "C01", "vo": "Drop it."}]})
        self.assertEqual(sb["style"], "auto")
        self.assertEqual(sb["voice"], "auto")


class TestIconsForAnyTopic(unittest.TestCase):
    def test_library_and_aliases(self):
        names, aliases = html.icon_table()
        self.assertGreaterEqual(len(names), 70)
        for word, want in {
            "phone": "phone",
            "black hole": "blackhole",
            "elephant": "elephant",
            "dog": "animal",
            "titanic": "ship",
            "banana": "banana",
            "pizza": "food",
            "tsunami": "wave",
            "bee": "insect",
            "salt": "crystal",
            "moon": "moon",
            "volcano": "volcano",
            "virus": "virus",
            "dna": "dna",
        }.items():
            self.assertEqual(html.icon_for(word), want, word)
        self.assertIsNone(html.icon_for("xyzzy"))

    def test_unknown_icon_is_an_error_with_hint(self):
        errs = html.validate("drop", {"a": {"icon": "xyzzy"}, "b": {"icon": "glass"}})
        self.assertEqual(len(errs), 1)
        self.assertIn("parts", errs[0])

    def test_parts_icon(self):
        good = {
            "parts": [
                {"k": "circle", "x": 0, "y": 0, "r": 0.6, "role": "hot"},
                {"k": "rect", "x": -1, "y": 0, "w": 2, "h": 0.3},
            ]
        }
        self.assertEqual(html.validate("title", {"icon": good}), [])
        self.assertTrue(html.validate("title", {"icon": {"parts": [{"k": "blob"}]}}))
        self.assertTrue(html.validate("title", {"icon": {"parts": []}}))

    def test_nested_icons_are_checked(self):
        p = {"steps": [{"icon": "phone", "label": "a"}, {"icon": "nope", "label": "b"}]}
        self.assertEqual(len(html.validate("process", p)), 1)


if __name__ == "__main__":
    unittest.main()


class TestIconProduction(unittest.TestCase):
    """Bộ đạo cụ production: đủ vật cho phòng thí nghiệm/đời sống, JS = Python khi khớp từ khoá, mọi icon hợp lệ."""

    WORDS = [
        "marathon runner",
        "vo2 max",
        "bench press",
        "protein shake",
        "google flow",
        "pull request",
        "ocr",
        "neural network",
        "liquid nitrogen",
        "vacuum chamber",
        "blue whale",
        "sonic boom",
        "heart rate",
        "sweat",
        "kettlebell swing",
        "pendulum swing",
        "magnifying glass",
        "glass of water",
        "ice water",
        "planet earth",
        "earth",
        "sleep",
        "coffee",
        "nuclear",
        "scale",
        "weight",
        "thermometer",
        "millimeter",
        "sound",
        "lab flask",
        "black hole",
        "scientist",
        "test tube",
        "steel ball",
        "lava",
        "titanic",
        "vaccine",
        "candle",
        "hourglass",
        "xyzzy",
        "the moon",
        "bee",
        "chart",
    ]

    def test_lab_and_life_props_exist(self):
        names = html.icon_table()[0]
        need = {
            "scientist",
            "flask",
            "testtube",
            "microscope",
            "telescope",
            "magnifier",
            "balance",
            "ruler",
            "earth",
            "bed",
            "cup",
            "hourglass",
            "speaker",
            "radiation",
            "umbrella",
            "chart",
            "syringe",
            "candle",
        }
        self.assertEqual(need - names, set())
        self.assertGreaterEqual(len(names), 180)

    @unittest.skipUnless(__import__("shutil").which("node"), "cần node")
    def test_js_and_python_resolve_words_identically(self):
        import json as _json
        import subprocess

        from vidlib.common import ROOT

        code = (
            "import {iconFor} from './engines/html/icons.js'; const w = JSON.parse(process.argv[1]); "
            "console.log(JSON.stringify(w.map(iconFor)));"
        )
        r = subprocess.run(
            ["node", "--input-type=module", "-e", code, _json.dumps(self.WORDS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        js = _json.loads(r.stdout)
        py = [html.icon_for(w) or "dot" for w in self.WORDS]
        self.assertEqual(js, py)
        got = dict(zip(self.WORDS, py))
        self.assertEqual(got["magnifying glass"], "magnifier")  # cụm dài thắng từ ngắn ("glass")
        self.assertEqual(got["glass of water"], "glass")
        self.assertEqual(got["kettlebell swing"], "kettlebell")
        self.assertEqual(got["pendulum swing"], "pendulum")

    @unittest.skipUnless(__import__("shutil").which("node"), "cần node")
    def test_every_icon_yields_valid_primitives(self):
        import subprocess

        from vidlib.common import ROOT

        code = (
            "import {ICONS} from './engines/html/icons.js'; const ok=['circle','rect','poly','line','arc']; let bad=[];"
            "for (const [k,f] of Object.entries(ICONS)) for (const fr of [0,9,40]) for (const p of [0,0.5,1]) {"
            " for (const q of f({f:fr,p})) { const s=JSON.stringify(q);"
            " if (!ok.includes(q.k) || s.includes('null') || s.includes('NaN')) bad.push(k); } }"
            "console.log(JSON.stringify([...new Set(bad)]));"
        )
        r = subprocess.run(["node", "--input-type=module", "-e", code], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(r.stdout.strip(), "[]")


class TestChannelProps(unittest.TestCase):
    """Đạo cụ theo các mảng của kênh (config/channel.json → universes A–D) + phòng thí nghiệm."""

    def test_every_icon_in_exactly_one_group(self):
        names = html.icon_table()[0]
        groups = html.icon_groups()
        flat = [n for items in groups.values() for n in items]
        self.assertEqual(sorted(names - set(flat)), [], "icon chưa có nhóm (thêm vào GROUPS trong icons_channel.js)")
        self.assertEqual(sorted(set(flat) - names), [], "nhóm nhắc tới icon không tồn tại")
        self.assertEqual(sorted({n for n in flat if flat.count(n) > 1}), [], "icon nằm ở nhiều nhóm")

    def test_universes_are_covered(self):
        groups = html.icon_groups()
        for key, need in {
            "running & body (A)": {"runner", "shoe", "stopwatch", "ecg", "lungs", "mitochondria"},
            "strength & fitness (B)": {"dumbbell", "barbell", "kettlebell", "lifter", "weightplate"},
            "AI visual & motion design (C)": {"camera", "clapper", "keyframe", "timeline", "sparkle", "waveform"},
            "developer tech & AI tools (D)": {"code", "terminal", "bug", "database", "branch", "scan", "network"},
            "lab & experiment": {"flask", "beaker", "burner", "belljar", "nitrogen", "gauge"},
        }.items():
            self.assertTrue(need <= set(groups[key]), key)

    def test_no_keyword_points_to_two_icons(self):
        seen, clash = {}, []
        for k, ic in html.icon_table()[1]:
            if seen.get(k, ic) != ic:
                clash.append(f"{k}: {seen[k]} / {ic}")
            seen.setdefault(k, ic)
        self.assertEqual(clash, [])

    def test_brief_lists_icons_by_group(self):
        h = brief.engine_help()
        for g in html.icon_groups():
            self.assertIn(g, h)
        self.assertIn("runner", h)
        self.assertIn("terminal", h)
