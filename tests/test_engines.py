"""Vòng 7: adapter chung, engine html/manim, style card, chấm điểm chủ đề. Không mở trình duyệt, không gọi mạng."""

import json
import os
import re
import tempfile
import unittest
from unittest import mock

from engines import adapter, html
from engines import manim as manim_engine
from vidlib import codeshot, storyboard, styles, textstyle
from vidlib.common import ROOT

NEW = [
    "flat-vector-black",
    "line-boil-black",
    "isometric-black",
    "hud-black",
    "synthwave-black",
    "sticker-explainer-black",
    "swiss-motion-black",
    "spy-titles-black",
    "pictogram-black",
    "scale-zoom-black",
    "flowchart-black",
    "sketchnote-black",
    "gallery-pointillist-black",
    "physics-diagram-black",
]


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


def lum(hex_):
    r, g, b = (int(hex_.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


class TestHtmlEngine(unittest.TestCase):
    def test_beats_and_looks_match_js(self):
        js = re.search(r"export const BEATS = \{([^}]*)\}", read("engines", "html", "beats.js")).group(1)
        self.assertEqual([b.strip() for b in js.split(",")], list(html.BEATS))
        raw = re.search(r"const RAW = \{([^}]*)\}", read("engines", "html", "looks.js")).group(1)
        self.assertEqual([b.strip() for b in raw.split(",")], list(html.LOOKS))
        self.assertEqual(set(html.PARAMS), set(html.BEATS))

    def test_demo_data_is_valid_for_every_beat(self):
        demo = json.loads(read("engines", "html", "demo.json"))
        for b in html.BEATS:
            self.assertEqual(html.validate(b, demo[b]), [], b)
        self.assertTrue(html.validate("drop", {}))
        self.assertTrue(html.validate("nope", {}))

    def test_no_content_or_absolute_times_in_engine_code(self):
        """Mã engine không chứa nội dung video (chữ của ý tưởng mẫu) — dữ liệu chỉ nằm trong demo.json/storyboard."""
        for fn in ("core.js", "beats.js", "looks.js", "icons.js"):
            src = read("engines", "html", fn)
            for word in ("Leidenfrost", "steel ball", "1,000", "ice water", "Lava"):
                self.assertNotIn(
                    word, src.replace("'steel ball', 'iron ball'", "").replace("'ice water', 'water'", ""), f"{fn}: {word}"
                )
        self.assertNotIn("Leidenfrost", read("engines", "manim", "scenes.py"))

    def test_no_network_in_engine_pages(self):
        for fn in os.listdir(os.path.join(ROOT, "engines", "html")):
            if fn.endswith((".js", ".html")):
                self.assertIsNone(re.search(r"https?://", read("engines", "html", fn)), fn)

    def test_job_is_data_driven(self):
        with tempfile.TemporaryDirectory() as d:
            spec = adapter.ShotSpec(
                sid="C01",
                engine="html",
                scene="title",
                params={"title": "Any idea"},
                frames=30,
                style="hud-black",
                work=d,
                index=[2, 5],
            )
            job = adapter.load_job(adapter.get("html").job(spec))
        self.assertEqual(job["page"], "engines/html/index.html")
        self.assertEqual(job["look"]["look"], "hud")
        self.assertEqual(job["params"]["index"], [2, 5])
        self.assertEqual(job["look"]["palette"]["bg"], "#000000")
        self.assertEqual([f["family"] for f in job["fonts"]], ["StyleFont", "StyleMono"])
        self.assertIn("top", job["safe"])


class TestAdapter(unittest.TestCase):
    def test_four_engines_one_interface(self):
        self.assertEqual(set(adapter.ENGINE_NAMES), {"three", "html", "manim", "board"})
        for name in adapter.ENGINE_NAMES:
            e = adapter.get(name)
            for attr in ("scenes", "rev", "job", "render", "meta", "text_crops"):
                self.assertTrue(callable(getattr(e, attr)), f"{name}.{attr}")
            self.assertTrue(e.scenes())
            self.assertRegex(e.rev(), r"^[0-9a-f]{12}$")
        with self.assertRaises(ValueError):
            adapter.get("remotion")

    def test_engine_of_follows_style_then_falls_back(self):
        sh = lambda sc, **kw: {"id": "C01", "code": {"scene": sc, **kw}}  # noqa: E731
        self.assertEqual(codeshot.engine_of(sh("thermometer"), "forward"), "three")
        self.assertEqual(codeshot.engine_of(sh("drop"), "forward"), "html")
        self.assertEqual(codeshot.engine_of(sh("outro"), "forward"), "three")  # style cũ: outro vẫn là cảnh three.js
        self.assertEqual(codeshot.engine_of(sh("outro"), "swiss-motion-black"), "html")
        self.assertEqual(codeshot.engine_of(sh("graph"), "physics-diagram-black"), "manim")
        self.assertEqual(codeshot.engine_of(sh("drop"), "physics-diagram-black"), "html")  # beat manim không có → html
        self.assertEqual(codeshot.engine_of(sh("graph", engine="html"), "physics-diagram-black"), "html")
        self.assertTrue(codeshot.is_3d(sh("drop")))
        self.assertFalse(codeshot.is_3d({"id": "C01", "code": {"engine": "board"}}))

    def test_storyboard_validates_engine_params(self):
        base = {
            "topic": "t",
            "style": "hud-black",
            "shots": [
                {"id": "C01", "beat": "hook", "mode": "code", "target_sec": 2, "code": {"scene": "counter", "params": {}}}
            ],
        }
        errs, _ = storyboard.validate(storyboard.normalize(base))
        self.assertTrue(any("thiếu params: to" in e for e in errs), errs)
        base["shots"][0]["code"]["params"] = {"to": 5}
        errs, _ = storyboard.validate(storyboard.normalize(base))
        self.assertEqual(errs, [])
        base["shots"][0]["code"] = {"scene": "nope", "params": {}}
        errs, _ = storyboard.validate(storyboard.normalize(base))
        self.assertTrue(any("không có cảnh/beat 'nope'" in e for e in errs), errs)

    def test_manim_job_and_meta_without_rendering(self):
        with tempfile.TemporaryDirectory() as d:
            spec = adapter.ShotSpec(
                sid="C05",
                engine="manim",
                scene="graph",
                frames=60,
                style="physics-diagram-black",
                work=d,
                params={"title": "Curve", "points": [[0, 1], [1, 0]]},
            )
            jp = adapter.get("manim").job(spec)
            job = adapter.load_job(jp)
            meta = manim_engine.meta(jp)
        self.assertEqual(job["font"]["family"], "Montserrat")
        self.assertEqual(job["tokens"]["palette"]["bg"], "#000000")
        self.assertIn("Curve", meta["texts"])
        self.assertTrue(all(0 <= c["f"] < 60 for c in meta["cues"]))
        self.assertTrue(manim_engine.validate("graph", {}))


class TestStyleCards(unittest.TestCase):
    REQUIRED = (
        "name",
        "description",
        "source",
        "code_engine",
        "tags",
        "palette",
        "not",
        "pacing",
        "marks",
        "transitions",
        "sfx_pack",
        "music",
        "voice_persona",
        "thumbnail",
        "flow",
        "font",
        "black_min",
    )

    def test_cards_complete(self):
        for sid in NEW:
            st = textstyle.load_style(sid)
            for k in self.REQUIRED:
                self.assertTrue(st.get(k), f"{sid}: thiếu {k}")
            self.assertIn(st["code_engine"], ("html", "manim"))
            self.assertGreaterEqual(len(st["not"]), 3, sid)
            for k in ("medium", "look", "motion"):
                self.assertTrue(st["flow"].get(k), f"{sid}: flow.{k}")
            for k in ("repo", "url", "sha", "license", "from", "how"):
                self.assertTrue(st["source"].get(k), f"{sid}: source.{k}")
            self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "fonts", st["font"])), sid)
            self.assertTrue(
                os.path.exists(os.path.join(ROOT, "styles", f"{sid}.md")), f"{sid}.md (python studio.py styles --cards)"
            )

    def test_black_background_and_at_most_three_colours(self):
        for sid in NEW:
            st = textstyle.load_style(sid)
            pal = {k: v for k, v in st["palette"].items() if not k.startswith("_")}
            self.assertEqual(pal["bg"].lower(), "#000000", sid)
            self.assertLessEqual(len([k for k in pal if k not in ("bg", "ink")]), 3, sid)
            self.assertGreater(lum(pal["ink"]), 0.5, f"{sid}: mực phải sáng trên nền đen")
            if "html" in st:
                self.assertEqual(st["html"]["palette"]["bg"].lower(), "#000000", sid)
                self.assertIn(st["html"]["look"], html.LOOKS, sid)

    def test_sfx_pack_uses_existing_sounds(self):
        from vidlib import sfx

        have = set(sfx.available())
        for sid in NEW:
            for cue, name in textstyle.load_style(sid)["sfx_pack"].items():
                self.assertIn(name, have, f"{sid}: {cue}→{name}")

    def test_sources_pinned(self):
        src = json.loads(read("vendor", "SOURCES.json"))["sources"]
        for name, s in src.items():
            self.assertRegex(s["sha"], r"^[0-9a-f]{40}$", name)
            self.assertTrue(s["license"] and s["url"].startswith("https://github.com/"), name)
        credits = read("docs", "CREDITS.md")
        for sid in NEW:
            repo = textstyle.load_style(sid)["source"]["repo"]
            self.assertIn(repo.split(" ")[0], credits, f"{sid}: {repo} chưa có trong docs/CREDITS.md")


class TestStyleSelection(unittest.TestCase):
    def test_topic_tags_pick_style(self):
        self.assertGreater(styles.score("scale-zoom-black", "how big is the sun compared to an atom"), 2)
        self.assertGreater(styles.score("physics-diagram-black", "the temperature and heat of a steel ball"), 1)
        self.assertGreater(styles.score("hud-black", "a robot in space under extreme pressure"), 2)
        self.assertEqual(styles.score("hud-black", "baking bread at home"), 0)
        top = styles.ranked({"topic": "How big is an atom compared to a planet?"})[0][0]
        self.assertEqual(top, "scale-zoom-black")

    def test_special_styles_never_auto_picked(self):
        # cơ chế vẫn còn cho style nào đặt "special": true — hiện không style nào dùng (gallery-pointillist đã vào auto)
        real = styles.info

        def fake(name):
            return {**real(name), "special": name == "hud-black"}

        with mock.patch.object(styles, "info", side_effect=fake), mock.patch.object(styles, "history", return_value=[]):
            self.assertNotIn("hud-black", [s for s, _ in styles.ranked({"topic": "space robot"})])
        self.assertFalse(any(styles.info(s)["special"] for s in styles.available()))

    def test_new_styles_in_rotation(self):
        av = styles.available()
        for sid in NEW:
            self.assertIn(sid, av)
            self.assertIn(sid, styles.PREFERENCE)
            self.assertIn(styles.engine(sid), ("html", "manim"))
        self.assertEqual(styles.engine("board-black"), "board")
        self.assertEqual(styles.engine("toon3d-lab"), "three")
        self.assertEqual(styles.engine("chalk"), "flow")


class TestNoForeignSkills(unittest.TestCase):
    def test_only_channel_skill_and_no_agent_dirs_in_vendor(self):
        """Không skill bên ngoài nào tự kích hoạt trong repo: .claude/skills chỉ có skill của kênh; vendor/ không có
        thư mục .claude/.agents/.codex/.cursor (plugin kaz-documentary do người dùng đưa vào từ vòng 6 là ngoại lệ)."""
        self.assertEqual(sorted(os.listdir(os.path.join(ROOT, ".claude", "skills"))), ["black-lab-toon"])
        bad = []
        for dp, dn, _ in os.walk(os.path.join(ROOT, "vendor")):
            dn[:] = [d for d in dn if d not in (".git", "node_modules")]
            bad += [os.path.join(dp, d) for d in dn if d in (".claude", ".agents", ".codex", ".cursor", ".claude-plugin")]
            if dp.count(os.sep) - ROOT.count(os.sep) > 5:
                dn[:] = []
        bad = [b for b in bad if "kaz-documentary" not in b]
        self.assertEqual(bad, [])
        skill = read(".claude", "skills", "black-lab-toon", "SKILL.md")
        for name in ("hyperframes", "lemo-opuscar", "mg-styles"):
            self.assertIn(name, skill.lower(), f"SKILL.md của kênh phải nói rõ KHÔNG dùng skill {name}")


if __name__ == "__main__":
    unittest.main()
