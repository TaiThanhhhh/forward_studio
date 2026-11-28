# ruff: noqa: E501 — chuỗi JS nhúng chạy bằng node, giữ nguyên dòng cho dễ đọc
"""Vòng 21: điểm neo bộ phận + bộ phận sống (rig2d/scene), chuyển cảnh zoom_through (portal + hậu kỳ), 3D frame.dive,
sổ dữ kiện có nguồn (facts), SEO đa nền tảng + brand-safety (seo), web search của brief, bí danh style."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

import numpy as np
from PIL import Image

from engines import adapter, html
from engines.html import rig2d
from vidlib import brief, facts, linter, partzoom, seo, spine, storyboard, styles, textstyle, ytupload
from vidlib.common import ROOT

NODE = shutil.which("node")


def _node(code):
    r = subprocess.run([NODE, "--input-type=module", "-e", code], capture_output=True, text=True, cwd=ROOT, timeout=60)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


@unittest.skipUnless(NODE, "cần node")
class TestRigPartsInNode(unittest.TestCase):
    def test_anchors_follow_pose_mirror_and_fallback(self):
        out = _node(
            "import * as R from './engines/html/rig2d.js';"
            "const a0 = R.rigAnchors('rig:adult:walk', {f: 0}), a9 = R.rigAnchors('rig:adult:walk', {f: 9});"
            "const L = R.rigAnchors('rig:adult:walk', {f: 0, args: {face: 'left'}});"
            "const owl = R.rigAnchors('rig:owl', {f: 3}), fish = R.rigAnchors('rig:fish', {f: 3});"
            "console.log(JSON.stringify({keys: Object.keys(a0), h0: a0.hand, h9: a9.hand, e: a0.eye, eL: L.eye,"
            " fishHand: R.partOf(fish, 'hand'), owlEye: owl.eye, parts: R.PARTS, organs: R.ORGANS}));")
        for k in ("head", "eye", "brain", "mouth", "chest", "heart", "lungs", "belly", "hand", "foot", "center"):
            self.assertIn(k, out["keys"])
        self.assertNotEqual(out["h0"], out["h9"])                    # bàn tay đổi chỗ theo chu kỳ bước
        self.assertAlmostEqual(out["eL"][0], -out["e"][0], places=6)  # quay trái = lật gương
        self.assertEqual(len(out["fishHand"]), 3)                     # loài không có tay → lùi về bộ phận gần nhất
        self.assertIsNotNone(out["owlEye"])
        self.assertEqual(tuple(out["parts"]), rig2d.parts())          # Python đọc đúng từ vựng JS
        self.assertEqual(tuple(out["organs"]), rig2d.organs())

    def test_xray_organs_talk_and_distance_cycle(self):
        out = _node(
            "import * as R from './engines/html/rig2d.js';"
            "const base = R.rigPrims('rig:adult', {f: 10});"
            "const xr = R.rigPrims('rig:adult', {f: 10, args: {xray: 1, organs: ['brain', 'heart', 'lungs', 'stomach', 'skeleton']}});"
            "const t0 = R.rigPrims('rig:kid', {f: 10}), t1 = R.rigPrims('rig:kid', {f: 10, args: {talk: 1}});"
            "const c0 = R.rigPrims('rig:dog:walk', {f: 10, args: {cycle: 0.1}}), c1 = R.rigPrims('rig:dog:walk', {f: 99, args: {cycle: 0.1}});"
            "const owl = R.rigPrims('rig:owl', {f: 0}), bird = R.rigPrims('rig:bird', {f: 0}), sci = R.rigPrims('rig:scientist', {f: 0});"
            "console.log(JSON.stringify({n0: base.length, nx: xr.length, organs: xr.filter((p) => p.organ).length,"
            " faded: xr.filter((p) => !p.fine && !p.organ).every((p) => (p.alpha ?? 1) < 0.5), anchorsLeak: xr.some((p) => p.anchor),"
            " talkDiff: JSON.stringify(t0) !== JSON.stringify(t1), cycleSame: JSON.stringify(c0.slice(0, 6)) === JSON.stringify(c1.slice(0, 6)),"
            " owl: owl.length, bird: bird.length, sci: sci.length, stride: R.strideOf('rig:adult', 'walk')}));")
        self.assertGreater(out["nx"], out["n0"])
        self.assertGreaterEqual(out["organs"], 5)
        self.assertTrue(out["faded"])
        self.assertFalse(out["anchorsLeak"])                           # marker neo không bao giờ bị vẽ
        self.assertTrue(out["talkDiff"])
        self.assertTrue(out["cycleSame"])                              # cùng quãng đường → cùng dáng chân (không trượt)
        self.assertNotEqual(out["owl"], out["bird"])                   # cú có đĩa mặt/túm lông → khác chim thường
        self.assertGreater(out["stride"], 0.3)

    def test_scene_beat_registers_part_anchors_with_minimal_ctx(self):
        out = _node(
            "import { BEATS } from './engines/html/beats.js';"
            "const logs = []; const anchors = {};"
            "const mk = (f) => ({ g: { save(){}, restore(){}, translate(){}, scale(){}, rotate(){}, set filter(v){}, get filter(){return 'none';} },"
            " W: 1080, H: 1920, N: 60, FPS: 30, f, fs: f, t: f / 30, u: f / 59, A: { top: 400, bottom: 1240, x0: 90, x1: 990, cx: 540 },"
            " L: { look: 'flat' }, clamp: (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), lerp: (a, b, t) => a + (b - a) * t,"
            " hash: () => 0.3, strSeed: () => 7, EASE: { smooth: (t) => t, back: (t) => t }, E: (t) => t, MO: {},"
            " k: () => 1, K: { halo(){}, arrow(){}, tag(){}, label(){} }, enter: (k, b, fn) => fn(),"
            " icon: (n, o) => logs.push(['icon', n, o.args && o.args.talk]), draw(){}, text: () => ({ x0: 0, x1: 100, y0: 0, y1: 40 }),"
            " anchor: (id, x, y, r) => { anchors[id] = [x, y, r]; },"
            " iconAnchors: (n, o) => ({ center: [o.x, o.y, o.s], eye: [o.x + 5, o.y - 30, 4] }), pickPart: (an, p) => an[p] || an.center });"
            "const P = { actors: [{ id: 'hero', icon: 'rig:adult', talk: true, x: 0.5, y: 0.6, size: 400 }],"
            " camera: [{ u: 1, at: 'hero.eye', zoom: 8 }], labels: [{ text: 'hi', of: 'hero.mouth', bubble: 'speech' }] };"
            "const S = BEATS.scene(mk(0), P); S.draw(mk(30));"
            "console.log(JSON.stringify({ ids: Object.keys(anchors), talk: logs.find((x) => x[0] === 'icon')[2] }));")
        self.assertIn("hero", out["ids"])
        self.assertIn("hero.eye", out["ids"])


class TestValidation(unittest.TestCase):
    def test_scene_part_refs_and_living_fields(self):
        ok = {"actors": [{"id": "hero", "icon": "rig:adult", "xray": 0, "organs": ["heart"], "keys": [{"u": 0.5, "xray": 1}],
                          "hold": "phone", "talk": [[0, 0.4]], "look_at": "cup.top", "focus": "heart"},
                         {"id": "cup", "icon": "coffee"}],
              "labels": [{"text": "Hmm", "of": "hero.head", "bubble": "thought"}],
              "camera": [{"u": 0.9, "at": "hero.eye", "zoom": 12}]}
        self.assertEqual(html.validate("scene", ok), [])
        bad = {"actors": [{"id": "hero", "icon": "rig:adult", "organs": ["spleen"], "talk": "yes"}],
               "labels": [{"text": "x", "bubble": "speech"}], "camera": [{"u": 1, "at": "ghost.eye", "zoom": 99}]}
        errs = " | ".join(html.validate("scene", bad))
        for frag in ("spleen", "xray > 0", "talk", "bong bóng cần `of`", "ghost", "zoom"):
            self.assertIn(frag, errs)

    def test_storyboard_zoom_through(self):
        def sb(through):
            return storyboard.normalize({"topic": "t", "shots": [
                {"id": "C01", "beat": "hook", "target_sec": 2, "mode": "code", "vo": "a",
                 "code": {"engine": "html", "scene": "scene", "params": {"actors": [{"id": "hero", "icon": "rig:adult"}]}}},
                {"id": "C02", "beat": "setup", "target_sec": 2, "mode": "code", "vo": "b", "transition_in": "zoom_through",
                 "through": through, "code": {"engine": "html", "scene": "title", "params": {"title": "x"}}}]})
        self.assertEqual(storyboard.validate(sb("hero.eye"))[0], [])
        self.assertEqual(storyboard.validate(sb([0.4, 0.3]))[0], [])
        self.assertTrue(any("ghost" in e for e in storyboard.validate(sb("ghost.eye"))[0]))
        self.assertTrue(any("bộ phận" in e for e in storyboard.validate(sb("hero.kneecap"))[0]))
        self.assertTrue(storyboard.validate(sb([2, 0.3]))[0])

    def test_stage_dive_validation(self):
        props = [{"id": "hero", "type": "mannequin"}]
        self.assertEqual(adapter.stage_dive_errors({"props": props, "frame": {"dive": {"of": "hero", "part": "eye"}}}), [])
        errs = adapter.stage_dive_errors({"props": props, "frame": {"dive": {"of": "bob", "part": "knee", "u": 2}}})
        self.assertEqual(len(errs), 3)


class TestPortalAndPost(unittest.TestCase):
    def test_spine_places_portal_and_avoids_adjacent_zooms(self):
        A = {"id": "C01", "code": {"engine": "html", "scene": "scene", "params": {"actors": [{"id": "hero", "icon": "rig:kid"}]}}}
        B = {"id": "C02", "transition_in": "zoom_through", "through": "hero.eye",
             "code": {"engine": "html", "scene": "scene", "params": {"actors": [{"id": "x", "icon": "cell"}]}}}
        C = {"id": "C03", "code": {"engine": "html", "scene": "title", "params": {"title": "t"}}}
        segs = [{"sid": s, "n": 60, "start_f": i * 60} for i, s in enumerate(("C01", "C02", "C03"))]
        ctx = spine.context(segs, {"C01": A, "C02": B, "C03": C}, "cosmic-flat-black", "portal-test", lambda s: True,
                            lambda s: {"scene": s["code"]["scene"], "params": s["code"]["params"]})
        self.assertEqual(ctx["C01"]["move_out"], "portal")
        self.assertTrue(ctx["C01"]["next"]["tile"]["portal"])
        self.assertEqual(ctx["C02"]["prev"]["tile"]["at"], "hero.eye")
        self.assertNotIn(ctx["C02"]["move_out"], spine.ZOOMS)          # không hai cú đổi cỡ liền nhau
        self.assertNotIn("portal", spine.ALL)                           # không bao giờ được bốc ngẫu nhiên

    def test_post_zoom_through_targets_point_and_opens_hole(self):
        a = Image.new("RGB", (108, 192), (20, 20, 30))
        a.paste((250, 40, 40), (70, 40, 80, 50))                        # "mắt" đỏ lệch tâm
        b = Image.new("RGB", (108, 192), (30, 200, 60))                 # cảnh sau xanh
        tgt = (75.0, 45.0, 5.0)
        last = np.asarray(partzoom.apply_out(a, 59, 60, tgt))
        self.assertGreater(last[96, 54, 0], 200)                        # điểm đích đã về giữa khung
        first = np.asarray(partzoom.apply_in(b, a, 0, tgt))
        self.assertGreater(first[96, 54, 1], 150)                       # tâm: cảnh sau lộ qua lỗ
        self.assertLess(first[2, 2, 1], 120)                            # góc: còn là shot trước
        late = np.asarray(partzoom.apply_in(b, a, partzoom.IN_FRAMES - 1, tgt))
        self.assertGreater(late[2, 2, 1], 150)                          # cuối chặng: lỗ phủ kín
        self.assertIs(partzoom.apply_in(b, a, partzoom.IN_FRAMES, tgt), b)

    def test_target_reads_engine_anchors(self):
        with tempfile.TemporaryDirectory() as proj:
            d = os.path.join(proj, "work", "code", "C01")
            os.makedirs(d)
            with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as fh:
                json.dump({"anchors_end": {"hero.eye": [600.0, 700.0, 30.0], "hero": [540, 900, 200]}}, fh)
            self.assertEqual(partzoom.target(proj, {"id": "C01"}, {"through": "hero.eye"}), (600.0, 700.0, 30.0))
            x, y, _ = partzoom.target(proj, {"id": "C01"}, {"through": [0.25, 0.5]})
            self.assertEqual((x, y), (270.0, 960.0))
            self.assertEqual(partzoom.target(proj, {"id": "C09"}, {"through": "nobody.eye"})[:2], (540.0, 960.0))


def _fact_sb():
    return {"title": "Venus day", "truth": "True",
            "sources": [{"id": "S1", "title": "Venus facts", "publisher": "NASA", "year": 2024, "url": "https://science.nasa.gov/venus"},
                        {"id": "S2", "title": "Thread", "url": "https://www.reddit.com/r/space/x"}],
            "claims": [{"id": "K1", "text": "A day on Venus lasts 243 Earth days", "value": 243, "unit": "days", "source": "S1"},
                       {"id": "K2", "text": "Life in Venus clouds", "source": "S2", "status": "hypothetical"}],
            "shots": [{"id": "C01", "vo": "A day on Venus lasts two hundred forty-three Earth days.", "claims": ["K1"],
                       "text_fx": [{"text": "243 DAYS"}]},
                      {"id": "C02", "vo": "Life floats in its clouds.", "claims": ["K2"]},
                      {"id": "C03", "vo": "Studies show it never rains, ninety times the pressure.",
                       "code": {"scene": "scene", "params": {"actors": [{"icon": "rig:adult", "size": 420}, {"icon": "door", "size": 120}]}}},
                      {"id": "C04", "vo": "The clock says 300.", "claims": ["K1"], "text_fx": [{"text": "300 DAYS"}]}]}


class TestFacts(unittest.TestCase):
    def test_lint_catches_the_credibility_problems(self):
        msgs = " | ".join(f"{i['where']}: {i['msg']}" for i in facts.lint(_fact_sb()))
        self.assertIn("nguồn S2", msgs)                                  # reddit = nguồn yếu
        self.assertIn("C02: claim K2 là hypothetical", msgs)             # giả định mà nói chắc
        self.assertIn("C03", msgs)                                       # "Studies show" + số không claim
        self.assertIn("tỉ lệ thực tế", msgs)                             # người 420px cạnh cửa 120px
        self.assertIn("C04: số trên màn", msgs)                          # 300 ≠ 243
        self.assertNotIn("C01:", msgs)                                   # shot đúng chuẩn: im lặng

    def test_research_cross_check_and_tiers(self):
        with tempfile.TemporaryDirectory() as proj:
            os.makedirs(os.path.join(proj, "work"))
            with open(os.path.join(proj, "work", "research.json"), "w", encoding="utf-8") as fh:
                json.dump({"urls": ["https://science.nasa.gov/venus"]}, fh)
            msgs = " ".join(i["msg"] for i in facts.lint(_fact_sb(), proj))
        self.assertIn("reddit.com/r/space/x không có trong kết quả tìm kiếm", msgs)
        self.assertEqual(facts.tier({"url": "https://www.nature.com/articles/x"}), "A")
        self.assertEqual(facts.tier({"url": "https://en.wikipedia.org/wiki/Venus"}), "C")
        self.assertEqual(facts.tier({"url": "https://medium.com/@a/b"}), "D")
        self.assertEqual(facts.sources({"sources": ["https://www.nasa.gov/x NASA page"]})[0]["url"], "https://www.nasa.gov/x")

    def test_cite_chip_and_publish_blocks(self):
        sb = _fact_sb()
        self.assertEqual(facts.cite_for(sb, sb["shots"][0]), "Source: NASA (2024)")
        self.assertIsNone(facts.cite_for(sb, {"id": "C09", "cite": False, "claims": ["K1"]}))
        self.assertIn("NASA (2024)", facts.description_block(sb))
        chip = facts.CiteChip(sb, 1080, 1920)
        img = Image.new("RGB", (1080, 1920), (0, 0, 0))
        out = np.asarray(chip.draw(img, sb["shots"][0], 30, 90))
        self.assertGreater(out[chip.cy - 20:chip.cy + 20].max(), 150)    # chip nằm giữa sân khấu và phụ đề
        self.assertEqual(out[:1200].max(), 0)
        self.assertIn("## Claim", facts.report_md(sb, facts.lint(sb)))


class TestProductionFixes(unittest.TestCase):
    def test_hedge_words_include_leading_idea(self):
        sb = {"claims": [{"id": "K1", "text": "x", "source": "S1", "status": "disputed"}],
              "sources": [{"id": "S1", "url": "https://www.nature.com/a"}],
              "shots": [{"id": "C01", "vo": "One leading idea: nerve sensors get damaged too.", "claims": ["K1"]}]}
        self.assertFalse([i for i in facts.lint(sb) if "rào đón" in i["msg"]])

    def test_rights_record_the_real_tts_provider(self):
        from vidlib import rights
        with tempfile.TemporaryDirectory() as proj:
            os.makedirs(os.path.join(proj, "audio"))
            open(os.path.join(proj, "audio", "vo.mp3"), "wb").close()
            with open(os.path.join(proj, "audio", "vo_alignment.json"), "w", encoding="utf-8") as fh:
                json.dump({"provider": "edge_tts"}, fh)
            ids = [u[0] if isinstance(u, (list, tuple)) else u.get("id") for u in rights.usage(proj, {"style_resolved": "forward"})]
            self.assertIn("voice:edge-tts", ids)
            self.assertNotIn("voice:elevenlabs", ids)
        self.assertTrue(any(a["id"] == "voice:edge-tts" for a in rights.ledger()["assets"]))
        self.assertIn("edge_tts", rights.ledger()["decisions"])
        self.assertEqual(html.validate("scene", {"actors": [{"id": "a", "icon": "rig:kid"}],
                                                 "labels": [{"text": "hi", "of": "a.head", "bubble": "speech", "side": "up"}]})[0][-30:],
                         "side là left|right (hướng đẩy bong bóng)."[-30:])


class TestSeo(unittest.TestCase):
    def _sb(self):
        return {"topic": "why do we dream", "title": "Why do we dream?", "claims": [{"id": "K1"}],
                "shots": [{"id": "C01", "vo": "Why do we dream? Your brain replays the day.", "code": {"scene": "title"}},
                          {"id": "C02", "vo": "Neurons fire.", "code": {"scene": "scene"}}],
                "publish": {"primary_keyword": "why do we dream", "localizations": {"es": {"title": "¿Por qué soñamos?"}},
                            "youtube_shorts": {"titles": ["Why Do We Dream? The Brain's Night Shift"],
                                               "description": "Why do we dream every night? Your brain sorts memories.",
                                               "hashtags": ["dreams", "brain", "sleep"], "tags": ["why do we dream"]}}}

    def test_score_brand_safety_and_lint_errors(self):
        sb = self._sb()
        sc, rows = seo.score(sb)
        self.assertGreaterEqual(sc, 80, rows)
        sb["publish"]["youtube_shorts"]["tags"].append("kurzgesagt style explainer")
        sb["shots"][1]["vo"] = "Like Veritasium said, neurons fire."
        aud, _ = seo.brand_hits(sb)
        self.assertEqual({n.lower() for _, n in aud}, {"kurzgesagt", "veritasium"})
        errs = [i for i in linter.lint_facts(sb) if i["level"] == "error"]
        self.assertEqual(len(errs), 2)
        self.assertFalse(seo.brand_hits({"shots": [{"vo": "A fern grows in the shade."}]})[0])   # từ thường không bị bắt

    def test_youtube_payload_category_synthetic_localizations_sources(self):
        sb = self._sb()
        sb["sources"] = [{"id": "S1", "publisher": "NIH", "year": 2023, "url": "https://www.nih.gov/x"}]
        pl = ytupload.build_payload(sb)
        st, sn = pl["body"]["status"], pl["body"]["snippet"]
        self.assertIs(st["containsSyntheticMedia"], False)               # toàn shot code → không phải cảnh thật
        self.assertEqual(sn["categoryId"], "27")                         # chủ đề não/giấc mơ → Education
        self.assertIn("Sources: NIH (2023)", sn["description"])
        self.assertEqual(pl["body"]["localizations"]["es"]["title"], "¿Por qué soñamos?")
        sb["shots"].append({"id": "C03", "vo": "x", "mode": "auto"})     # có clip Flow → chủ kênh phải quyết
        pl2 = ytupload.build_payload(sb)
        self.assertNotIn("containsSyntheticMedia", pl2["body"]["status"])
        self.assertTrue(pl2["synthetic_undecided"])


class _Blk(types.SimpleNamespace):
    pass


class TestBriefWebSearch(unittest.TestCase):
    def test_ask_uses_server_tools_and_resumes_pause_turn(self):
        calls = []
        r1 = _Blk(stop_reason="pause_turn", usage=_Blk(input_tokens=10, output_tokens=5), content=[
            _Blk(type="text", text="Let me check {not json}."),
            _Blk(type="server_tool_use", input={"query": "venus day length"}),
            _Blk(type="web_search_tool_result", content=[_Blk(url="https://science.nasa.gov/venus")])])
        r2 = _Blk(stop_reason="end_turn", usage=_Blk(input_tokens=20, output_tokens=50), content=[
            _Blk(type="web_fetch_tool_result", content=_Blk(url="https://science.nasa.gov/venus/facts")),
            _Blk(type="text", text='{"topic": "venus"}')])
        replies = [r1, r2]

        class _Stream:
            def __init__(self, kw):
                calls.append(kw)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def get_final_message(self):
                return replies[len(calls) - 1]

        fake = types.ModuleType("anthropic")
        fake.Anthropic = lambda: _Blk(beta=_Blk(messages=_Blk(stream=lambda **kw: _Stream(kw))))
        old = sys.modules.get("anthropic")
        sys.modules["anthropic"] = fake
        try:
            text = brief.ask("claude", "BRIEF")
        finally:
            if old is not None:
                sys.modules["anthropic"] = old
            else:
                sys.modules.pop("anthropic", None)
        self.assertEqual(json.loads(text), {"topic": "venus"})          # chỉ phần sau khối công cụ cuối
        self.assertEqual(len(calls), 2)
        self.assertEqual([t["type"] for t in calls[0]["tools"]], ["web_search_20260209", "web_fetch_20260209"])
        self.assertEqual(calls[1]["messages"][-1]["role"], "assistant")  # nối tiếp lượt dở, không thêm "continue"
        self.assertEqual(len(calls[1]["messages"]), 2)
        self.assertEqual(brief.LAST_RESEARCH["urls"], ["https://science.nasa.gov/venus", "https://science.nasa.gov/venus/facts"])
        self.assertEqual(brief.LAST_USAGE["tokens_out"], 55)

    def test_web_tools_can_be_disabled(self):
        os.environ["BRIEF_WEB_SEARCH"] = "0"
        try:
            self.assertEqual(brief.web_tools(), [])
        finally:
            os.environ.pop("BRIEF_WEB_SEARCH")


class TestStyleAliases(unittest.TestCase):
    def test_old_brand_ids_resolve_to_genre_styles(self):
        self.assertEqual(textstyle.canonical("kurzgesagt-black"), "cosmic-flat-black")
        style, _ = styles.resolve({"style": "school-of-life-black"}, "x")
        self.assertEqual(style, "essay-ink-black")
        for sid in ("cosmic-flat-black", "essay-ink-black", "bold-infographic-black"):
            st = textstyle.load_style(sid)
            blob = json.dumps({k: st.get(k) for k in ("name", "description", "tags", "flow")}).lower()
            for brand in ("kurzgesagt", "school of life", "infographics show", "psych2go", "ted-ed", "life noggin"):
                self.assertNotIn(brand, blob, sid)


if __name__ == "__main__":
    unittest.main()
