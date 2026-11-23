"""Vòng 6: engine board (evidence board) — màu không đảo BGR, đủ glyph, không mốc thời gian cứng trong mã, dàn cảnh từ
storyboard (beat_recipe), dấu đỏ 0–3 frame trước từ khoá, camera không đứng, đoạn chèn phim câm, 16:9, đường `cuts`."""
import glob
import math
import os
import re
import tempfile
import unittest

import numpy as np

from engines.board import camera, fonts, sprites
from engines.board import color as bcol
from engines.board.scene import Scene, fmt_like
from vidlib import boardplan, boardqa, sfx, storyboard, styles
from vidlib.common import FPS, ROOT

WORDS = ("Drop a thousand-degree ball into water. Steel glows from five hundred. At a thousand it is orange. "
         "You'd think the water heats up but the ice swallows the heat. It stays at zero.")


def _sb(style="board-black", assembly="board_spine"):
    shots = [
        {"id": "C01", "beat": "hook", "vo": "Drop a thousand-degree ball into water.", "target_sec": 2.0,
         "beat_recipe": "DOC_FOCUS", "board": {"lines": ["Lab notes", "glows from ≈ 525°C"], "circle": "≈ 525°C",
                                               "sync": "vo_word:thousand"}},
        {"id": "C02", "beat": "setup", "vo": "Steel glows from five hundred.", "target_sec": 2.0,
         "beat_recipe": "NUMBER_CARD", "board": {"number": "1,000°C", "from": 525, "sync": "vo_word:five",
                                                 "marks": [{"kind": "stamp", "text": "CONFIRMED",
                                                            "sync": "vo_word:glows"}]}},
        {"id": "C03", "beat": "escalate", "vo": "At a thousand it is orange.", "target_sec": 2.0,
         "beat_recipe": "NAME_TAG",
         "board": {"on": "C02", "text": "ORANGE-RED", "at": [0.5, 0.5], "sync": "vo_word:thousand"}},
        {"id": "C04", "beat": "twist", "vo": "You'd think the water heats up but the ice swallows the heat.",
         "target_sec": 2.5, "beat_recipe": "THESIS",
         "board": {"old": "You'd think it heats up.", "new": "It stays at 0°C", "strike_sync": "vo_word:swallows"}},
        {"id": "C05", "beat": "twist", "vo": "It stays at zero.", "target_sec": 1.5, "beat_recipe": "THESIS",
         "board": {"continue": True, "new_sync": "vo_word:stays"}},
        {"id": "C06", "beat": "outro", "vo": "", "target_sec": 1.2, "beat_recipe": "NETWORK_REVEAL"},
    ]
    return storyboard.normalize({"topic": "t", "style": style, "assembly": assembly, "shots": shots,
                                 "outro": {"teaser": "Liquid nitrogen vs boiling water"}})


def _tl_vo(sb, outro=1.5):
    """Timeline + VO giả: mỗi shot có VO một câu, từ rải đều trong shot."""
    t, segs, lines = 0.0, [], []
    for i, s in enumerate(sb["shots"]):
        n = int(round(s["target_sec"] * FPS))
        segs.append({"sid": s["id"], "index": i, "start_f": int(round(t * FPS)), "n": n, "dur": n / FPS,
                     "transition": "cut", "punches": [], "zoom_base": 1.0})
        ws = s["vo"].split()
        if ws:
            words = [{"w": w, "start": round(t + 0.1 + k * (n / FPS - 0.3) / len(ws), 3),
                      "end": round(t + 0.1 + (k + 1) * (n / FPS - 0.3) / len(ws), 3)} for k, w in enumerate(ws)]
            lines.append({"text": s["vo"], "shots": [i], "start": words[0]["start"], "end": words[-1]["end"],
                          "words": words})
        elif lines:
            lines[-1]["shots"].append(i)
        t += n / FPS
    no = int(round(outro * FPS))
    segs.append({"sid": "OUTRO", "index": len(segs), "start_f": int(round(t * FPS)), "n": no, "dur": outro,
                 "transition": "glitch", "punches": [], "zoom_base": 1.0})
    total = int(round(t * FPS)) + no
    return {"segments": segs, "frames": total, "duration": total / FPS}, {"lines": lines}


def _plan(size=None, assembly="board_spine"):
    sb = _sb(assembly=assembly)
    tl, vo = _tl_vo(sb)
    p = boardplan.Plan(tempfile.gettempdir(), sb, tl, vo, "board-black", {}, size)
    p.build()
    return p.to_json()


class Color(unittest.TestCase):
    def test_hex_to_bgr_never_swaps(self):
        self.assertEqual(bcol.rgb("#d0312d"), (208, 49, 45))
        self.assertEqual(bcol.bgr("#d0312d"), (45, 49, 208))
        a = np.zeros((2, 2, 3), np.uint8)
        a[..., 2] = 200  # BGR: kênh 2 là đỏ
        self.assertEqual(tuple(bcol.to_rgb(a)[0, 0]), (200, 0, 0))

    def test_rendered_accent_is_red(self):
        b = _plan()
        sc = Scene(b)
        q = boardqa.color_rows(b, sc.frame)
        self.assertTrue(q, "phải có vòng tròn/dây đỏ để đo")
        for r in q:
            self.assertTrue(r["ok"], r)
            R, G, B = r["median_rgb"]
            self.assertGreater(R, B + 60)

    def test_sprite_premultiplied_red(self):
        from PIL import Image  # noqa: PLC0415
        s = bcol.sprite(Image.new("RGBA", (2, 2), (208, 49, 45, 255)))
        self.assertEqual(tuple(s[0, 0]), (45, 49, 208, 255))


class Glyphs(unittest.TestCase):
    def test_fonts_vendored_with_license(self):
        for f in ("FreeMonoBold.ttf", "Caladea-Bold.ttf", "LICENSE-freefont.txt", "LICENSE-caladea.txt"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, "assets", "fonts", f)), f)

    def test_no_tofu_for_symbols(self):
        for role in ("mono", "serif", "hand"):
            self.assertEqual(fonts.missing("1,000°C ×1000 ≈ 525°C → 0.3 s — “ok” DON'T", role), [], role)

    def test_plan_texts_have_glyphs(self):
        b = _plan()
        self.assertTrue(b["qa"]["texts"])
        self.assertFalse([t for t in b["qa"]["texts"] if t["missing"]])


class NoHardcodedTimes(unittest.TestCase):
    def test_engine_has_no_timeline_constants(self):
        """Mốc thời gian chỉ nằm trong board.json: cấm 't > 85.3', 'T0 = 1896/30', 'st = 69.25'… trong engine."""
        pat = re.compile(r"\b(?:t|lt|st|T0|T1|S2)\s*(?:[<>]=?|==|=)\s*\d{2,}(?:\.\d+)?\b|/\s*30\b")
        for p in glob.glob(os.path.join(ROOT, "engines", "board", "*.py")):
            with open(p, encoding="utf-8") as f:
                for k, ln in enumerate(f, 1):
                    self.assertIsNone(pat.search(ln.split("#")[0]), f"{os.path.basename(p)}:{k}: {ln.strip()}")


class Plan(unittest.TestCase):
    def test_recipes_make_items_marks_and_camera(self):
        b = _plan()
        kinds = {it["kind"] for it in b["items"]}
        self.assertTrue({"paper", "number", "thesis"} <= kinds)
        self.assertEqual(len([it for it in b["items"] if it["kind"] == "thesis"]), 1)  # C05 nối tiếp C04
        mk = {m["kind"] for m in b["marks"]}
        self.assertTrue({"circle", "stamp", "tag"} <= mk)
        self.assertTrue(b["returns"])                                    # NETWORK_REVEAL: nhãn quay lại
        self.assertEqual(b["overlays"][-1]["kind"], "title_glitch")       # outro
        self.assertIn("Next:", " ".join(b["overlays"][-1]["title_lines"]))
        ts = [k["t"] for k in b["camera"]]
        self.assertEqual(ts, sorted(ts))
        self.assertEqual(ts[0], 0.0)

    def test_marks_lead_keyword_by_0_to_3_frames(self):
        b = _plan()
        self.assertTrue(b["qa"]["marks"])
        for m in b["qa"]["marks"]:
            self.assertTrue(0 <= m["lead_f"] <= 3, m)

    def test_camera_never_still(self):
        b = _plan()
        sec, _, _ = boardqa.stills(b)
        self.assertLess(sec, 0.4)

    def test_number_countup_format(self):
        self.assertEqual(fmt_like("1,000°C", 909.4), "909°C")
        self.assertEqual(fmt_like("0.3 s", 0.12), "0.1 s")
        self.assertEqual(fmt_like("×1000", 525), "×525")

    def test_tags_readable_before_camera_leaves(self):
        b = _plan()
        for r in b["qa"]["reads"]:
            self.assertGreaterEqual(r["read_sec"], 0.6, r)

    def test_late_keyword_is_flagged(self):
        sb = _sb()
        sb["shots"][1]["board"]["marks"][0]["sync"] = "vo_word:hundred"   # từ cuối câu → không kịp đọc
        tl, vo = _tl_vo(sb)
        p = boardplan.Plan(tempfile.gettempdir(), sb, tl, vo, "board-black", {})
        p.build()
        self.assertTrue(any("CONFIRMED" in n and "từ khoá sớm hơn" in n for n in p.notes))
        self.assertTrue(any(r["read_sec"] < 0.6 for r in p.reads))

    def test_stamp_limit(self):
        sb = _sb()
        for s in sb["shots"][:3]:
            s["board"].setdefault("marks", []).append({"kind": "stamp", "text": "MYTH", "sync": "t:0.3"})
        tl, vo = _tl_vo(sb)
        p = boardplan.Plan(tempfile.gettempdir(), sb, tl, vo, "board-black", {})
        p.build()
        self.assertLessEqual(len([m for m in p.marks if m["kind"] == "stamp"]), 2)

    def test_landscape_16x9(self):
        b = _plan(size=(1920, 1080))
        self.assertEqual((b["width"], b["height"]), (1920, 1080))
        self.assertGreater(b["world"]["w"], b["world"]["h"])
        f = Scene(b).frame(20)
        self.assertEqual(f.shape, (1080, 1920, 3))

    def test_cuts_assembly_skips_media(self):
        sb = _sb(assembly="cuts")
        sb["shots"].insert(1, storyboard.normalize({"topic": "t", "shots": [{
            "id": "C09", "beat": "setup", "vo": "", "target_sec": 1.0, "subject": "a glass",
            "start_frame": {"desc": "a glass"}, "action": [{"do": "water ripples"}]}]})["shots"][0])
        tl, vo = _tl_vo(sb)
        p = boardplan.Plan(tempfile.gettempdir(), sb, tl, vo, "board-black", {})
        p.build()
        self.assertFalse([it for it in p.items if it["kind"] == "media"])


class UserImage(unittest.TestCase):
    def test_public_domain_image_card(self):
        from PIL import Image  # noqa: PLC0415
        with tempfile.TemporaryDirectory() as d:
            Image.new("RGB", (300, 400), (120, 120, 120)).save(os.path.join(d, "portrait.jpg"))
            sb = _sb()
            sb["shots"].insert(1, storyboard.normalize({"topic": "t", "shots": [{
                "id": "C09", "beat": "setup", "vo": "", "target_sec": 1.5, "beat_recipe": "REVEAL_PHOTO",
                "board": {"image": "portrait.jpg", "gray": True}}]})["shots"][0])
            self.assertEqual(sb["shots"][1]["code"]["engine"], "board")       # không cần clip Flow
            tl, vo = _tl_vo(sb)
            p = boardplan.Plan(d, sb, tl, vo, "board-black", {})
            p.build()
            it = next(i for i in p.items if i["id"] == "C09")
            self.assertEqual(it["kind"], "image")
            self.assertAlmostEqual((it["h"] - 80) / (it["w"] - 32), 400 / 300, places=2)
            b = p.to_json()
            b["items"] = [{**x, "path": os.path.join(d, "portrait.jpg")} if x["id"] == "C09" else x for x in b["items"]]
            Scene(b).frame(70)

    def test_missing_image_is_error(self):
        sb = storyboard.normalize({"topic": "t", "shots": [{"id": "C01", "beat": "hook", "vo": "x",
                                                            "board": {"image": "assets/user/nope.jpg"}}]})
        errs, _ = storyboard.validate(sb)
        self.assertTrue(any("assets/user" in e for e in errs))


class Schema(unittest.TestCase):
    def test_native_recipe_becomes_board_code_shot(self):
        sb = _sb()
        s = sb["shots"][1]
        self.assertEqual(s["mode"], "code")
        self.assertEqual(s["code"]["engine"], "board")
        errs, _ = storyboard.validate(sb)
        self.assertEqual(errs, [])

    def test_missing_params_are_errors(self):
        sb = storyboard.normalize({"topic": "t", "shots": [{"id": "C01", "beat": "hook", "vo": "x",
                                                            "beat_recipe": "NUMBER_CARD", "board": {}}]})
        errs, _ = storyboard.validate(sb)
        self.assertTrue(any("NUMBER_CARD" in e for e in errs))

    def test_flow_shot_stays_flow(self):
        sb = storyboard.normalize({"topic": "t", "shots": [{"id": "C01", "beat": "hook", "vo": "x",
                                                            "beat_recipe": "REVEAL_PHOTO",
                                                            "start_frame": {"desc": "a glass"}, "action": ["drop"]}]})
        self.assertNotEqual(sb["shots"][0]["mode"], "code")


class Styles(unittest.TestCase):
    def test_board_styles_in_rotation(self):
        av = styles.available()
        for s in ("board-black", "chalk-case-black", "lab-notebook-black", "silent-film-black"):
            self.assertIn(s, av)
            self.assertEqual(boardplan.assembly({"assembly": "auto"}, s), "board_spine")
            tok = boardplan.tokens(s)
            self.assertEqual(tok["accent"].lower(), "#d0312d")
            self.assertLess(sum(bcol.rgb(tok["bg"])) / 3, 25)              # nền đen / gần đen
        self.assertEqual(boardplan.assembly({"assembly": "auto"}, "forward"), "cuts")
        self.assertEqual(boardplan.assembly({"assembly": "cuts"}, "board-black"), "cuts")

    def test_silent_film_mono_except_red(self):
        from engines.board import vintage  # noqa: PLC0415
        spec = {"panels": [{"kind": "tableau", "dur": 1, "actors": [
            {"kind": "figure", "x": 0.3, "y": 0.9, "scale": 0.5, "wig": True},
            {"kind": "ball", "x": 0.7, "y": 0.5, "r": 0.08, "hot": 1.0}]},
            {"kind": "intertitle", "dur": 1, "lines": ["It dances."]}]}
        v = vintage.Insert(spec, 270, 480, FPS, 30, boardplan.tokens("silent-film-black"))
        rgb = bcol.to_rgb(v.frame(3)).astype(int)
        sat = rgb.max(-1) - rgb.min(-1)
        red = (rgb[..., 0] > rgb[..., 2] + 60)
        self.assertTrue(red.any())                                          # đỏ accent còn giữ
        self.assertLess(((sat > 40) & ~red).mean(), 0.01)                   # còn lại là đơn sắc bạc


class Sfx(unittest.TestCase):
    def test_param_sfx(self):
        a = sfx.load("typing:0.8", 48000)
        self.assertGreater(len(a), int(0.8 * 48000))
        self.assertEqual(sfx.split_name("projector:3.4"), ("projector", 3.4))
        self.assertEqual(sfx.level_db("typing:1.2"), sfx.level_db("typing"))


class Camera(unittest.TestCase):
    def test_zoom_log_interp_and_roundtrip(self):
        keys = [{"t": 0, "cx": 0, "cy": 0, "zoom": 1.0, "rot": 0}, {"t": 1, "cx": 0, "cy": 0, "zoom": 4.0, "rot": 0,
                                                                      "ease": "linear"}]
        self.assertAlmostEqual(camera.at(keys, 0.5)[2], 2.0, places=6)     # trung bình hình học
        C = (100, 200, 1.7, 3.0)
        p = camera.to_world(camera.to_screen((321, 654), C, 1080, 1920), C, 1080, 1920)
        self.assertAlmostEqual(p[0], 321, places=6)
        self.assertAlmostEqual(p[1], 654, places=6)

    def test_media_geom_matches_sprite(self):
        tok = boardplan.tokens("board-black")
        spr, rect = sprites.media_card(480, 853.33, tok)
        self.assertEqual(rect, sprites.media_geom(480, 853.33, tok)[2])
        self.assertTrue(math.isclose(rect[2] - rect[0], 480))


if __name__ == "__main__":
    unittest.main()
