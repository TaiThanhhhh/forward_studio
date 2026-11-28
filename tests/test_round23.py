# ruff: noqa: E501 — chuỗi JS nhúng chạy bằng node, giữ nguyên dòng cho dễ đọc
"""Vòng 23: đầu ra gọn (lean), cổng giữ chân (hook / re-hook / diễn viên), giọng Edge riêng + tông theo vai, người tả
thực nhìn chính diện / sau lưng, deadlift, đạp xe gối gập ra trước."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from vidlib import lean, qagate, retention, tts
from vidlib.common import ROOT

NODE = shutil.which("node")


def _node(code):
    r = subprocess.run([NODE, "--input-type=module", "-e", code], capture_output=True, text=True, cwd=ROOT, timeout=90)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _sb(vos, actors=None):
    shots = []
    for i, v in enumerate(vos):
        p = {"actors": (actors or {}).get(i, [{"id": "x", "icon": "dot"}])}
        shots.append({"id": f"C{i + 1:02d}", "vo": v, "code": {"engine": "html", "scene": "scene", "params": p}})
    return {"title": "t", "topic": "t", "shots": shots}


class TestRetention(unittest.TestCase):
    def test_hook(self):
        self.assertTrue(retention.hook_check(_sb(["Why does your heart beat faster when you're scared?"]))[1])
        self.assertTrue(retention.hook_check(_sb(["Running wrecks a few red blood cells with every step."]))[1])
        bad = retention.hook_check(_sb(["In this video we will look at how the heart works and many other things today."]))
        self.assertFalse(bad[1])
        self.assertIn("mở đầu chậm", bad[0])

    def test_script(self):
        ok = _sb(["Why is ice so slippery?", "Most people say water.", "It's a thin film.", "But here's the weird part.",
                  "Pressure barely matters.", "So ice is slippery all by itself."])
        self.assertTrue(retention.script_check(ok)[1])
        bad = _sb(["Why is ice so slippery?", "Most people say water.", "It's a thin film.", "Pressure barely matters.",
                   "It is cold.", "Smash that like button and subscribe for more videos about ice and other things okay."])
        val, passed = retention.script_check(bad)
        self.assertFalse(passed)
        self.assertIn("re-hook", val)
        self.assertIn("xin tương tác", val)

    def test_cast_needs_two_views(self):
        side = {i: [{"id": "a", "icon": "rig:athlete:run"}] for i in range(4)}
        self.assertFalse(retention.cast_check(_sb(["a"] * 4, side))[1])
        mixed = dict(side)
        mixed[2] = [{"id": "a", "icon": "rig:athlete:run", "view": "front"}]
        self.assertTrue(retention.cast_check(_sb(["a"] * 4, mixed))[1])

    def test_non_english_skipped(self):
        sb = _sb(["Điều gì xảy ra nếu bạn chạy marathon với cái bụng rỗng và không ăn gì suốt cả buổi sáng?"])
        self.assertFalse(retention.english(sb))
        self.assertTrue(all(ok is not False for _v, ok in retention.checks(sb).values()))

    def test_gate_blocks_new_checks(self):
        lv = {r["label"]: r["level"] for r in qagate.classify({
            "hook 2 giây đầu": ("x", False), "kịch bản giữ chân": ("x", False), "diễn viên đa dạng": ("x", False),
            "chữ không đè hình": ("x", False), "chuyển động (không như slide)": ("x", False)})}
        self.assertEqual(set(lv.values()), {"red"})


class TestLean(unittest.TestCase):
    def test_prune_keeps_only_what_is_posted(self):
        d = tempfile.mkdtemp()
        try:
            for rel, size in [("storyboard.json", 10), ("audio/vo.mp3", 10), ("audio/vo.prev-x.mp3", 10), ("out/final.mp4", 10),
                              ("out/captions.srt", 5), ("out/versions/v001/final.mp4", 10), ("out/deliver/tiktok/a.mp4", 10),
                              ("work/state.json", 5), ("work/code/C01/frames/f0001.jpg", 10), ("work/mix.wav", 2_000_000),
                              ("qa/report.html", 10), ("thumbnails/T1_9x16.png", 10), ("scripts.html", 10), ("publish.md", 10),
                              ("clips/C02.mp4", 10)]:
                p = os.path.join(d, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as fh:
                    fh.write(b"x" * size)
            lean.prune(d, log=lambda *a: None)
            have = sorted(os.path.relpath(os.path.join(r, f), d).replace(os.sep, "/") for r, _, fs in os.walk(d) for f in fs)
            self.assertEqual(have, ["audio/vo.mp3", "clips/C02.mp4", "out/captions.srt", "out/final.mp4", "storyboard.json",
                                    "work/state.json"])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_post_md_has_every_platform(self):
        sb = {"title": "Test", "topic": "t", "shots": [], "publish": {
            "youtube_shorts": {"titles": ["A title about sleep"], "description": "Sleep matters.", "hashtags": ["sleep"],
                               "tags": ["sleep science"], "pinned_comment": "How long do you sleep?"},
            "tiktok": {"caption": "Sleep 😴", "hashtags": ["sleep", "fyp", "learn"]},
            "instagram_reels": {"caption": "Sleep", "hashtags": ["sleep"]}}}
        md = lean.post_md("x", sb, "XANH")
        for part in ("## YouTube Shorts", "## TikTok", "## Instagram / Facebook Reels", "Made for kids = **No**", "A title about sleep"):
            self.assertIn(part, md)


class TestVoices(unittest.TestCase):
    def test_every_pool_voice_has_its_own_edge_voice(self):
        cfg = tts.voice_cfg()
        pool = cfg["pools"]["en"]
        specs = [tts.edge_spec(cfg, {"id": v["id"]})["voice"] for v in pool]
        self.assertEqual(len(specs), len(set(specs)))
        self.assertGreaterEqual(len(specs), 25)

    def test_tone_segments_follow_beats(self):
        lines = [{"text": "a", "beat": "hook"}, {"text": "b", "beat": "hook"}, {"text": "c", "beat": "setup"},
                 {"text": "d", "beat": "payoff"}]
        segs = tts._tone_segments(lines, {})
        self.assertEqual([(s[0], len(s[1]), s[2]) for s in segs], [(0, 2, "hook"), (2, 1, "setup"), (3, 1, "payoff")])
        tone = tts.voice_cfg()["edge_tone"]
        self.assertGreater(tone["hook"]["rate"], tone["payoff"]["rate"])


@unittest.skipUnless(NODE, "cần node")
class TestPeopleInNode(unittest.TestCase):
    def test_front_back_views_and_new_cast(self):
        out = _node(
            "import * as R from './engines/html/rig2d.js'; import { FRONT_ACTIONS } from './engines/html/rig_human.js';"
            "const sp = ['coach', 'lifterf', 'bigguy', 'elder', 'student', 'office', 'cyclist', 'medic', 'trailrunner', 'athlete'], bad = [];"
            "for (const s of sp) for (const a of FRONT_ACTIONS) for (const v of ['front', 'back']) for (const f of [0, 13]) {"
            " const pr = R.rigPrims(`rig:${s}:${a}:${v}`, { f });"
            " for (const q of pr) { const n = [q.x, q.y, q.rx, q.ry, ...(q.pts || []).flat()]; if (!n.every((x) => x === undefined || Number.isFinite(x))) bad.push(`${s}:${a}:${v}`); } }"
            "const an = R.rigAnchors('rig:lifter:squat:front', { f: 5 });"
            "const side = R.rigPrims('rig:athlete:idle', { f: 0 }).length, front = R.rigPrims('rig:athlete:idle:front', { f: 0 }).length;"
            "const kn = R.rigAnchors('rig:cyclist:cycle', { f: 9 }), dl = R.rigPrims('rig:lifter:deadlift', { f: 3 }).length;"
            "console.log(JSON.stringify({ bad: [...new Set(bad)], keys: Object.keys(an), side, front, kneeAhead: kn.knee[0] > kn.hip[0], dl, parse: R.parseRig('rig:coach:wave:front') }));")
        self.assertEqual(out["bad"], [])
        for k in ("head", "hand", "knee", "foot", "chest", "spine", "thigh"):
            self.assertIn(k, out["keys"])
        self.assertNotEqual(out["side"], out["front"])
        self.assertTrue(out["kneeAhead"])              # đạp xe: gối ở PHÍA TRƯỚC hông (trước đây gập ngược)
        self.assertGreater(out["dl"], 30)
        self.assertEqual(out["parse"]["view"], "front")


if __name__ == "__main__":
    unittest.main()
