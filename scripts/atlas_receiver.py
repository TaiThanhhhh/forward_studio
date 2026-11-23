"""Bộ nhận cục bộ cho việc chụp 3D Style Atlas (Futurepedia) — chỉ nghe 127.0.0.1, chỉ nhận từ trang atlas.

  python scripts/atlas_receiver.py [--port 8777]

Trang atlas (chạy `scripts/atlas_capture.js` trong Console) POST từng style tới http://127.0.0.1:<port>/save →
ghi `vendor/3d-style-atlas/raw/NN-<slug>.json` (nguyên văn, không sửa). Prompt mỗi style ~100 KB nên không đi qua
clipboard tay. Thư mục raw/ bị gitignore (nội dung thuộc Futurepedia/HubSpot Media — chỉ dùng nội bộ).
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "vendor", "3d-style-atlas", "raw")
ORIGINS = {"https://www.futurepedia.io", "https://futurepedia.io"}
MAX_BODY = 4 * 1024 * 1024
FIELDS = ("number", "name", "category", "tag", "description", "shown_here", "good_for", "prompt_full",
          "source_url", "capture_method")


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "style"


def save(rec):
    n = int(rec["number"])
    if not 1 <= n <= 99:
        raise ValueError("number ngoài 1..99")
    out = {k: rec.get(k, "") for k in FIELDS}
    out["number"] = n
    out["slug"] = slugify(rec.get("name"))
    out["captured_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out["prompt_chars"] = len(out["prompt_full"] or "")
    out["incomplete"] = not (out["prompt_full"] and out["name"] and out["description"])
    os.makedirs(RAW, exist_ok=True)
    p = os.path.join(RAW, f"{n:02d}-{out['slug']}.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, p)
    return p, out


class H(BaseHTTPRequestHandler):
    def _cors(self):
        o = self.headers.get("Origin", "")
        if o in ORIGINS:
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "content-type")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Vary", "Origin")

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):  # noqa: N802
        if self.headers.get("Origin", "") not in ORIGINS or self.path != "/save":
            self.send_response(403)
            self.end_headers()
            return
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_BODY:
            self.send_response(413)
            self._cors()
            self.end_headers()
            return
        try:
            rec = json.loads(self.rfile.read(n).decode("utf-8"))
            p, out = save(rec)
            body = json.dumps({"ok": True, "file": os.path.relpath(p, ROOT), "chars": out["prompt_chars"],
                               "incomplete": out["incomplete"]}).encode()
            code = 200
            print(f"[atlas] #{out['number']:02d} {out['name']} · {out['prompt_chars']} ký tự", flush=True)
        except Exception as e:  # noqa: BLE001
            body, code = json.dumps({"ok": False, "error": str(e)}).encode(), 400
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8777)
    a = ap.parse_args(argv)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), H)
    print(f"[atlas] nhận tại http://127.0.0.1:{a.port}/save → {RAW}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
