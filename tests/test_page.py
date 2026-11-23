"""scripts.html: cấu trúc + selftest nút copy/phím tắt bằng headless browser (nếu máy có Chrome/Edge)."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers import demo
from vidlib import compiler, linter, page


def find_browser():
    cands = [shutil.which(n) for n in ("chrome", "google-chrome", "chromium", "msedge")]
    cands += [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    return next((c for c in cands if c and os.path.exists(c)), None)


class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.sb = compiler.compile_all(demo())
        cls.path = page.build(cls.sb, cls.tmp.name, linter.lint(cls.sb), {})
        with open(cls.path, encoding="utf-8") as f:
            cls.html = f.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_cards_and_order(self):
        for s in self.sb["shots"]:
            card = self.html.split(f'id="card-{s["id"]}"')[1].split("</section>")[0]
            pos = [card.find(k) for k in ("①", "③", "④")]
            self.assertTrue(all(p >= 0 for p in pos) and pos == sorted(pos), s["id"])
            if s["mode_resolved"] == "frames_start_end":
                self.assertIn("②", card)
                self.assertLess(card.find("①"), card.find("②"))
                self.assertLess(card.find("②"), card.find("③"))
        self.assertIn("FRAMES · Start+End", self.html)
        self.assertIn("INGREDIENTS · REF_RUNNER", self.html)
        self.assertIn("KHÔNG cần tự tạo — lấy từ clip C07", self.html)

    def test_ui_features(self):
        self.assertIn("Copy style bible", self.html)
        self.assertIn("Copy cả cảnh", self.html)
        self.assertIn("0/16 clip", self.html)
        self.assertRegex(self.html, r"try\{st=JSON\.parse\(localStorage")
        self.assertIn("k==='j'", self.html)
        self.assertIn("k==='c'", self.html)
        self.assertIn("clips/", self.html)

    def test_prompts_escaped_and_complete(self):
        n_copy = len(re.findall(r'data-copy="p\d+"', self.html))
        self.assertGreaterEqual(n_copy, 16 + 2)  # mỗi cảnh ≥1 + ingredients
        self.assertNotIn("<script>alert", self.html)
        self.assertIn("Audio: complete silence.", self.html)

    @unittest.skipUnless(find_browser(), "không có Chrome/Edge")
    def test_selftest_in_headless_browser(self):
        url = Path(self.path).resolve().as_uri() + "?selftest=1"
        with tempfile.TemporaryDirectory() as prof:
            r = subprocess.run([find_browser(), "--headless=new", "--disable-gpu", f"--user-data-dir={prof}",
                                "--virtual-time-budget=3000", "--dump-dom", url], capture_output=True, timeout=90)
        dom = r.stdout.decode("utf-8", "replace")
        m = re.search(r'<pre id="selftest">(.*?)</pre>', dom, re.S)
        self.assertIsNotNone(m, dom[-500:])
        self.assertIn('"pass":true', m.group(1), m.group(1))


if __name__ == "__main__":
    unittest.main()

