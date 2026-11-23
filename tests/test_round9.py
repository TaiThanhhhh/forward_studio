"""Vòng 9 (audit + sửa): cổng QA đỏ/vàng/xanh chặn xuất, spec file BT.709/faststart đo bằng ffprobe, gói nền tảng,
version + manifest, sổ quyền, chi phí, dấu vân tay mã nguồn, lệnh CLI."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from vidlib import cost, deliver, encode, manifest, pipeline, qagate, rights
from vidlib.common import ffbin, run

_TMP = None


def tiny_mp4(path, w=1080, h=1920, sec=1.0, tone=True):
    """MP4 thật nhỏ, encode bằng tham số chung của tool (tiếng sine ~ −14 LUFS)."""
    args = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate=30:duration={sec}"]
    if tone:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={sec}", "-af", "volume=-9dB"]
    args += ["-vf", encode.TO_YUV, *encode.video_args("master", 30), *(encode.audio_args() if tone else []),
             "-shortest", *encode.mux_args(), path]
    run(args, "ffmpeg (test)")
    return path


def setUpModule():
    global _TMP
    _TMP = tempfile.mkdtemp(prefix="studio-r9-")


def tearDownModule():
    shutil.rmtree(_TMP, ignore_errors=True)


class Gate(unittest.TestCase):
    def test_levels(self):
        rows = qagate.classify({"fps": ("29", False), "OCR đọc được": ("1/2", False), "kích thước": ("ok", True),
                                "nguồn Flow ≥ 720p": ("360x640", None)})
        lv = {r["label"]: r["level"] for r in rows}
        self.assertEqual(lv["fps"], "red")                      # nằm trong qa.blocking
        self.assertEqual(lv["OCR đọc được"], "yellow")          # không chặn
        self.assertEqual(lv["nguồn Flow ≥ 720p"], "yellow")     # không đo được / cảnh báo
        self.assertEqual(qagate.verdict(rows), "red")
        self.assertEqual(qagate.summary(rows)["red"], 1)

    def test_audio_rows_true_peak_has_no_slack(self):
        r = qagate.audio_checks({"lufs": -14.1, "true_peak": -0.8, "lra": 6}, -14, -1.0)
        self.assertTrue(r["loudness (LUFS tích hợp)"][1])
        self.assertFalse(r["true peak"][1])

    def test_red_gate_stops_pipeline_with_exit_12(self):
        self.assertEqual(pipeline.EXIT["qa_failed"], 12)
        self.assertLess(pipeline.STAGES.index("qa"), pipeline.STAGES.index("publish"))
        self.assertLess(pipeline.STAGES.index("publish"), pipeline.STAGES.index("deliver"))


class Spec(unittest.TestCase):
    def test_tool_encode_meets_spec(self):
        p = tiny_mp4(os.path.join(_TMP, "a.mp4"))
        rows = qagate.spec_checks(p)
        bad = {k: v for k, v in rows.items() if not v[1]}
        self.assertEqual(bad, {})
        self.assertTrue(qagate.moov_first(p))

    def test_broken_file_is_red(self):
        p = os.path.join(_TMP, "broken.mp4")
        with open(p, "wb") as fh:
            fh.write(b"\x00" * 48)
        rows = qagate.classify(qagate.spec_checks(p))
        self.assertEqual(qagate.verdict(rows), "red")
        from vidlib.common import valid_media
        self.assertFalse(valid_media(p))


class Deliver(unittest.TestCase):
    def test_presets_have_sources_and_safe_zones(self):
        c = deliver.cfg()
        for n, p in c["presets"].items():
            self.assertIn("safe", p, n)
            self.assertIn("cover", p, n)
            self.assertTrue(p.get("ai_label"), n)
        self.assertEqual(set(c["default"]), {"youtube_shorts", "instagram_reels", "tiktok"})

    def test_verify_shorts_and_tiktok(self):
        p = tiny_mp4(os.path.join(_TMP, "v.mp4"), sec=2.0)
        for name in ("youtube_shorts", "tiktok"):
            rows = qagate.classify(deliver.verify(p, deliver.cfg()["presets"][name]))
            reds = [r for r in rows if r["level"] == "red" and "loudness" not in r["label"]]
            self.assertEqual(reds, [], name)

    def test_wrong_size_is_red(self):
        p = tiny_mp4(os.path.join(_TMP, "small.mp4"), w=540, h=960)
        rows = qagate.classify(deliver.verify(p, deliver.cfg()["presets"]["youtube_shorts"]))
        self.assertIn("red", {r["level"] for r in rows if "khung" in r["label"]})


class Versions(unittest.TestCase):
    def test_new_version_only_when_final_changes(self):
        proj = os.path.join(_TMP, "proj")
        os.makedirs(os.path.join(proj, "out"), exist_ok=True)
        fin = os.path.join(proj, "out", "final.mp4")
        tiny_mp4(fin, w=320, h=568, tone=False)
        sb = {"topic": "t", "style_resolved": "forward", "shots": []}
        v1, m = manifest.write(proj, sb)
        v1b, _ = manifest.write(proj, sb)
        self.assertEqual((v1, v1b), ("v001", "v001"))
        self.assertIn("commit", m["git"])
        self.assertTrue(m["versions"]["ffmpeg"])
        tiny_mp4(fin, w=320, h=568, sec=1.5, tone=False)
        v2, _ = manifest.write(proj, sb)
        self.assertEqual(v2, "v002")
        self.assertTrue(os.path.exists(os.path.join(proj, "out", "versions", "v001", "final.mp4")))


class Rights(unittest.TestCase):
    def test_no_is_red_unknown_is_yellow(self):
        rows = qagate.classify(rights.checks([("brand:refs", "x"), ("voice:elevenlabs", "vo"), ("font:Anton", "f")]))
        lv = {r["label"]: r["level"] for r in rows}
        self.assertEqual(lv["quyền thương mại BỊ CẤM: brand:refs"], "red")
        self.assertEqual(lv["quyền: voice:elevenlabs"], "yellow")      # gói ElevenLabs chưa chốt
        self.assertEqual(lv["quyền: font:Anton"], "green")

    def test_decision_resolves(self):
        with mock.patch.object(rights, "ledger", return_value={"decisions": {"elevenlabs_plan": "creator"},
                                                               "assets": [{"id": "voice:elevenlabs", "license": "x",
                                                                           "commercial": "decision:elevenlabs_plan"}]}):
            self.assertEqual(rights.commercial(rights.entry("voice:elevenlabs")), "yes")

    def test_ai_disclosure(self):
        self.assertTrue(rights.ai_disclosure([("clip:flow", "")])["need"]["youtube"].startswith("BẮT BUỘC"))
        self.assertIn("không bắt buộc", rights.ai_disclosure([])["need"]["tiktok"])


class Cost(unittest.TestCase):
    def test_summary(self):
        s = cost.summarize([{"kind": "tts", "chars": 800}, {"kind": "tts", "chars": 800, "cached": True},
                            {"kind": "llm", "model": "claude-opus-5-5", "tokens_in": 1_000_000, "tokens_out": 0},
                            {"kind": "render", "engine": "three", "sec": 12.5}])
        self.assertEqual(s["tts_chars"], 800)
        self.assertEqual(s["tts_cached"], 1)
        self.assertAlmostEqual(s["usd_known"], 4.0, places=2)
        self.assertEqual(s["render_sec"]["three"], 12.5)


class Fingerprint(unittest.TestCase):
    def test_code_rev_tracks_vidlib_content(self):
        a = pipeline.code_rev()
        with mock.patch("builtins.open", mock.mock_open(read_data=b"changed")):
            b = pipeline.code_rev()
        self.assertNotEqual(a, b)


class Cli(unittest.TestCase):
    def test_typo_does_not_create_project(self):
        import studio
        import contextlib
        import io
        with mock.patch.object(pipeline, "Run") as R, contextlib.redirect_stdout(io.StringIO()):
            rc = studio.main(["stauts"])
        self.assertEqual(rc, 2)
        R.assert_not_called()

    def test_ffmpeg_found(self):
        self.assertTrue(os.path.exists(ffbin("ffmpeg")) or shutil.which("ffmpeg"))


if __name__ == "__main__":
    unittest.main()


class Schema(unittest.TestCase):
    def test_migrate_old_storyboard(self):
        from vidlib import storyboard
        sb, steps = storyboard.migrate({"topic": "t"})
        self.assertEqual(sb["version"], storyboard.SCHEMA_VERSION)
        self.assertEqual(steps, ["v1→v2", "v2→v3"])
        self.assertIn("seed", sb)
        sb2, steps2 = storyboard.migrate(dict(sb))
        self.assertEqual(steps2, [])
        self.assertEqual(sb2["seed"], sb["seed"])          # ổn định: chạy lại không đổi seed


class ReplaceRetry(unittest.TestCase):
    """Windows khoá file đang được UI stream → ghi đè phải thử lại thay vì chết giữa chừng (lỗi lượt xray Phần C)."""

    def test_retries_then_succeeds(self):
        from vidlib import common
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        src, dst = os.path.join(d, "a.part"), os.path.join(d, "a.mp4")
        open(src, "w").close()
        real, calls = os.replace, []

        def flaky(a, b):
            calls.append(1)
            if len(calls) < 3:
                raise PermissionError(5, "Access is denied")
            return real(a, b)
        with mock.patch("os.replace", flaky):
            common.replace_retry(src, dst, wait=0)
        self.assertTrue(os.path.exists(dst))
        self.assertEqual(len(calls), 3)

    def test_gives_clear_error(self):
        from vidlib import common
        with mock.patch("os.replace", side_effect=PermissionError(5, "Access is denied")):
            with self.assertRaises(common.StudioError) as cm:
                common.replace_retry("x", "y.mp4", tries=2, wait=0)
        self.assertIn("đang mở", str(cm.exception))
