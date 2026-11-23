"""Map tên file clip → shot."""
import os
import tempfile
import time
import unittest

from vidlib import ingest, storyboard


def _sb(n):
    sb = storyboard.normalize({"topic": "t", "shots": [{"start_frame": "a", "action": "b"} for _ in range(n)]})
    for s in sb["shots"]:
        s["mode_resolved"] = "frames_start"
    return sb


class Names(unittest.TestCase):
    def test_shot_id_from_name(self):
        for name, want in [("C01.mp4", "C01"), ("c1.mov", "C01"), ("C07_v2.mp4", "C07"), ("C12 take 3.mp4", "C12"),
                           ("c003.webm", "C03"), ("Generated_video.mp4", None), ("clip.mp4", None), ("C.mp4", None)]:
            self.assertEqual(ingest.shot_id_from_name(name), want, name)


class Mapping(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.proj = self.tmp.name
        os.makedirs(os.path.join(self.proj, "clips"))
        now = time.time()
        files = {"C01.mp4": now - 50, "c3.mov": now - 40, "flow_older.mp4": now - 30, "Generated_newer.mp4": now - 10,
                 "_hidden.mp4": now, "notes.txt": now}
        for n, t in files.items():
            p = os.path.join(self.proj, "clips", n)
            open(p, "wb").close()
            os.utime(p, (t, t))

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_by_name_then_download_time(self):
        rows = ingest.scan(self.proj, _sb(5))
        got = {r["sid"]: (os.path.basename(r["path"]), r["how"]) for r in rows}
        self.assertEqual(got["C01"], ("C01.mp4", "tên file"))
        self.assertEqual(got["C03"], ("c3.mov", "tên file"))
        self.assertEqual(got["C02"], ("flow_older.mp4", "thời gian tải về"))  # cũ hơn → shot thiếu đầu tiên
        self.assertEqual(got["C04"], ("Generated_newer.mp4", "thời gian tải về"))
        self.assertNotIn("C05", got)
        self.assertTrue(ingest.needs_confirm(rows))
        self.assertIn("thời gian tải về", ingest.table(rows))

    def test_saved_map_is_reused(self):
        rows = ingest.scan(self.proj, _sb(5))
        ingest.save_map(self.proj, rows)
        rows2 = ingest.scan(self.proj, _sb(5))
        self.assertFalse(ingest.needs_confirm(rows2))
        self.assertEqual({r["sid"]: r["how"] for r in rows2}["C02"], "đã xác nhận")

    def test_newer_named_file_wins(self):
        p = os.path.join(self.proj, "clips", "C01_v2.mp4")
        open(p, "wb").close()
        rows = ingest.scan(self.proj, _sb(5))
        self.assertEqual(os.path.basename(ingest.as_dict(rows)["C01"]), "C01_v2.mp4")

    def test_code_shots_ignored(self):
        sb = _sb(3)
        sb["shots"][1]["mode_resolved"] = "code"
        sb["shots"][1]["code"] = {"template": "counter"}
        rows = ingest.scan(self.proj, sb)
        self.assertNotIn("C02", ingest.as_dict(rows))


if __name__ == "__main__":
    unittest.main()
