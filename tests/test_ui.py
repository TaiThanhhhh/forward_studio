"""Studio UI (ui/server): chặn path traversal, Range, danh sách trắng lệnh job, chốt Host/CSRF, API đọc dữ liệu."""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from ui.server import app
from ui.server.services import files, jobs


class TestFiles(unittest.TestCase):
    def test_traversal_blocked(self):
        for bad in ("../.env", "..\\.env", "a/../../.env", "/../../windows/win.ini"):
            with self.assertRaises(files.Forbidden):
                files.resolve("projects", bad)
        with self.assertRaises(files.Forbidden):
            files.resolve("root", "x")                    # gốc không có trong danh sách

    def test_range(self):
        self.assertEqual(files.parse_range("bytes=0-99", 1000), (0, 99))
        self.assertEqual(files.parse_range("bytes=900-", 1000), (900, 999))
        self.assertEqual(files.parse_range("bytes=-100", 1000), (900, 999))
        self.assertIsNone(files.parse_range("bytes=2000-", 1000))
        self.assertIsNone(files.parse_range("items=0-1", 1000))


class TestJobWhitelist(unittest.TestCase):
    def build(self, kind, params):
        return jobs.Manager.build(None, kind, params)

    def test_video_argv(self):
        argv, _, slug, script = self.build("video", {"target": "What if you never slept?", "dry_run": True,
                                                     "look_ok": True, "style": "xray3d-black", "flow": False,
                                                     "from": "render"})
        self.assertEqual(argv[:3], ["video", "What if you never slept?", "--no-open"])
        for x in ("--dry-run", "--look-ok", "--no-flow"):
            self.assertIn(x, argv)
        self.assertEqual(argv[argv.index("--style") + 1], "xray3d-black")
        self.assertEqual(argv[argv.index("--from") + 1], "render")
        self.assertEqual(slug, "what-if-you-never-slept")
        self.assertIsNone(script)

    def test_rejects_bad_input(self):
        for params in ({"target": "--help"}, {"target": ""}, {"target": "a\nb"}, {"target": "x", "style": "nope"},
                       {"target": "x", "from": "nope"}, {"target": "x", "ai": "gpt"}, {"target": "x", "voice": "a;rm -rf"}):
            with self.assertRaises(jobs.JobError, msg=str(params)):
                self.build("video", params)
        with self.assertRaises(jobs.JobError):
            self.build("tool", {"name": "rm"})
        with self.assertRaises(jobs.JobError):
            self.build("ideas", {"theme": "x", "pick": "1;2"})
        with self.assertRaises(jobs.JobError):
            self.build("shell", {})


class TestHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.MANAGER = jobs.Manager()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        data = r.read()
        c.close()
        return r.status, data

    def test_health_and_static(self):
        st, data = self.req("GET", "/api/health")
        self.assertEqual(st, 200)
        self.assertTrue(json.loads(data)["ok"])
        st, data = self.req("GET", "/")
        self.assertEqual(st, 200)
        self.assertIn(b"/app/main.js", data)

    def test_host_and_csrf_guards(self):
        st, _ = self.req("GET", "/api/health", headers={"Host": "evil.example"})
        self.assertEqual(st, 403)
        st, _ = self.req("POST", "/api/jobs", body=b"{}", headers={"Content-Type": "application/json"})
        self.assertEqual(st, 403)
        st, _ = self.req("GET", "/api/file?root=projects&path=../.env")
        self.assertEqual(st, 403)
        st, _ = self.req("GET", "/..%2F.env")
        self.assertIn(st, (403, 404))

    def test_catalog_endpoints(self):
        st, data = self.req("GET", "/api/styles")
        self.assertEqual(st, 200)
        ids = {s["id"] for s in json.loads(data)["items"]}
        self.assertIn("xray3d-black", ids)
        st, data = self.req("GET", "/api/stages")
        self.assertIn("render", json.loads(data)["stages"])
        st, data = self.req("GET", "/api/plan?topic=what%20happens%20inside%20your%20heart")
        self.assertEqual(st, 200)
        self.assertIn("style", json.loads(data))
        st, _ = self.req("GET", "/api/projects/..%2F..%2Fetc")
        self.assertEqual(st, 404)

    def test_bad_job_is_400(self):
        st, data = self.req("POST", "/api/jobs", body=json.dumps({"kind": "video", "params": {"target": "-x"}}).encode(),
                            headers={"Content-Type": "application/json", "X-Studio-Client": "web"})
        self.assertEqual(st, 400)
        self.assertIn("error", json.loads(data))


if __name__ == "__main__":
    unittest.main()


class Round9Security(unittest.TestCase):
    """AUD-701/702: target có ký tự điều khiển hoặc trông như đường dẫn thư mục bị từ chối; worker không chết."""

    def test_target_validation(self):
        from ui.server.services import jobs as J
        for bad in ("a\x00b", "../ui", "..", "ui", "-x", "line\nbreak"):
            with self.assertRaises(J.JobError, msg=repr(bad)):
                J._check_target(bad)
        self.assertEqual(J._check_target("What happens if you drop ice into lava?"),
                         "What happens if you drop ice into lava?")


class Round10Usability(unittest.TestCase):
    """WP-U vòng 10: sbedit (kiểm/ghi/patch/restore), lưu .env cục bộ an toàn, catalog schema, API v2."""

    def test_sbedit_extract_check_patch_and_restore(self):
        import os
        import tempfile

        from vidlib import sbedit

        sample = {
            "topic": "What happens to your heart during a sprint?",
            "title": "Sprint Heart",
            "style": "flat-vector-black",
            "shots": [
                {"id": "C01", "beat": "hook", "mode": "code", "vo": "Your heart jumps to 157 beats per minute.",
                 "target_sec": 3.0, "code": {"scene": "title", "params": {"title": "157 BPM"}}},
                {"id": "C02", "beat": "escalate", "mode": "code", "vo": "Blood pumps faster every second.",
                 "target_sec": 3.0, "code": {"scene": "counter", "params": {"to": 157, "unit": "BPM"}}},
                {"id": "C03", "beat": "payoff", "mode": "code", "vo": "Then it recovers in two minutes.",
                 "target_sec": 3.0, "code": {"scene": "fact", "params": {"text": "Recovers fast"}}},
            ],
        }
        wrapped = "Here is the storyboard:\n```json\n" + json.dumps(sample, indent=2) + "\n```\nEnjoy!"
        data, start, notes = sbedit.extract_json(wrapped)
        self.assertEqual(data["title"], "Sprint Heart")
        self.assertTrue(notes)
        with tempfile.TemporaryDirectory() as td:
            rep = sbedit.import_text(td, wrapped, note="test import")
            self.assertTrue(rep.get("saved"))
            self.assertTrue(os.path.exists(os.path.join(td, "storyboard.json")))
            p = sbedit.patch(td, "C02", sets={"code.params.to": 180})
            self.assertTrue(p.get("saved"))
            self.assertTrue(p.get("backup"))
            with open(os.path.join(td, "storyboard.json"), encoding="utf-8") as fh:
                cur = json.load(fh)
            self.assertEqual(cur["shots"][1]["code"]["params"]["to"], 180)
            hs = sbedit.history(td)
            self.assertGreaterEqual(len(hs), 1)
            res = sbedit.restore(td, hs[0]["id"])
            self.assertTrue(res.get("saved"))
            with open(os.path.join(td, "storyboard.json"), encoding="utf-8") as fh:
                cur2 = json.load(fh)
            self.assertEqual(cur2["shots"][1]["code"]["params"]["to"], 157)

    def test_save_env_whitelist_and_no_secret_leak(self):
        import os
        import tempfile

        from ui.server.services import system

        with tempfile.TemporaryDirectory() as td:
            ep = os.path.join(td, ".env")
            res = system.save_env({"keys": {"GEMINI_API_KEY": "secret-val-123"}}, path=ep)
            self.assertTrue(res["ok"])
            self.assertNotIn("secret-val-123", json.dumps(res))
            with open(ep, encoding="utf-8") as fh:
                self.assertIn("GEMINI_API_KEY=secret-val-123", fh.read())
            with self.assertRaises(ValueError):
                system.save_env({"keys": {"PATH": "/evil"}}, path=ep)

    def test_catalog_schema_has_round10_data(self):
        from ui.server.services import catalog

        sc = catalog.schema()
        self.assertGreaterEqual(len(sc["beats"]), 15)
        self.assertGreaterEqual(len(sc["verbs"]), 50)
        self.assertGreaterEqual(len(sc["metaphors"]), 150)
        self.assertGreaterEqual(len(sc["round10_styles"]), 7)
        self.assertIn("dachshund", sc["creatures3d"].get("species", ()))
        self.assertIn("dog", sc["rig2d"].get("species", ()))
