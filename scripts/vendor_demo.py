"""Chạy demo GỐC của một repo trong vendor/ để xác nhận nó render được trên máy này (vòng 7, bước 2).

Không cài gì của repo nguồn, không chạy script của họ: chỉ mở trang demo trong Edge/Chromium headless (Playwright đã có
sẵn trong tool), gọi hàm "vẽ frame tại thời điểm t" của trang rồi chụp. MỌI request không tới 127.0.0.1 bị chặn và ghi
lại (=> biết demo có gọi mạng lúc render hay không). File phục vụ chỉ nằm trong thư mục repo nguồn.

  python scripts/vendor_demo.py <repo> <trang.html[?query]> --ready "<biểu thức JS>" --draw "<JS, dùng biến t>"
         --t 1,4,8 [--size 1920x1080] [--map /node_modules/three/=vendor/three/] [--out qa/sources/<repo>]
"""

import argparse
import contextlib
import functools
import http.server
import json
import os
import sys
import threading
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "vendor")


class _Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".json": "application/json",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".woff2": "font/woff2",
        ".wasm": "application/wasm",
    }
    maps = {}

    def log_message(self, *a):
        pass

    def translate_path(self, path):
        clean = urllib.parse.unquote(path.split("?", 1)[0].split("#", 1)[0])
        for prefix, target in self.maps.items():  # vd /node_modules/three/build/ → vendor/three/
            if clean == prefix:  # thế đúng MỘT file (vd font repo nguồn không kèm)
                return target
            if prefix.endswith("/") and clean.startswith(prefix):
                return os.path.join(target, clean[len(prefix) :].replace("/", os.sep))
        return super().translate_path(path)


@contextlib.contextmanager
def serve(directory, maps):
    _Handler.maps = maps
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Handler, directory=directory))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield srv.server_address[1]
    finally:
        srv.shutdown()
        srv.server_close()


def run(repo, page, ready, draw, times, size, out, maps, channel="msedge", wait=120):
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    base = os.path.join(VENDOR, repo)
    os.makedirs(out, exist_ok=True)
    blocked, missing, errors, shots = [], [], [], []
    w, h = size
    with serve(base, maps) as port, sync_playwright() as p:
        args = ["--use-angle=d3d11", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"]
        try:
            br = p.chromium.launch(channel=channel, headless=True, args=args)
        except Exception:  # noqa: BLE001
            br = p.chromium.launch(headless=True, args=args)
        ctx = br.new_context(viewport={"width": w, "height": h}, service_workers="block")

        def gate(route):
            u = route.request.url
            if u.startswith((f"http://127.0.0.1:{port}/", "data:", "blob:", "about:")):
                return route.continue_()
            blocked.append(u[:160])
            return route.abort()

        ctx.route("**/*", gate)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)[:300]))
        pg.on("response", lambda r: missing.append(r.url.split(f":{port}", 1)[-1][:160]) if r.status == 404 else None)
        t0 = time.time()
        pg.goto(f"http://127.0.0.1:{port}/{page}", timeout=wait * 1000)
        try:
            pg.wait_for_function(ready, timeout=wait * 1000)
        except Exception as ex:  # noqa: BLE001
            errors.append(f"không sẵn sàng sau {wait}s: {str(ex)[:120]}")
        boot = time.time() - t0
        per = []
        for t in times:
            t1 = time.time()
            try:
                pg.evaluate(f"async (t) => {{ {draw} }}", t)
            except Exception as ex:  # noqa: BLE001
                errors.append(f"t={t}: {str(ex)[:200]}")
                continue
            dst = os.path.join(out, f"t_{t:05.2f}.jpg")
            pg.screenshot(path=dst, type="jpeg", quality=90)
            per.append(round(time.time() - t1, 3))
            shots.append(os.path.relpath(dst, ROOT).replace(os.sep, "/"))
        br.close()
    rep = {
        "repo": repo,
        "page": page,
        "size": [w, h],
        "times": times,
        "frames": shots,
        "boot_sec": round(boot, 2),
        "sec_per_frame": per,
        "blocked_requests": sorted(set(blocked)),
        "missing_files": sorted(set(missing))[:20],
        "page_errors": errors[:8],
        "ok": len(shots) == len(times),
    }
    with open(os.path.join(out, "run.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("page")
    ap.add_argument("--ready", default="true")
    ap.add_argument("--draw", required=True)
    ap.add_argument("--t", default="1,4,8")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--out")
    ap.add_argument("--wait", type=int, default=60)
    ap.add_argument("--map", action="append", default=[], help="/tiền-tố-url/=đường/dẫn/tính/từ/repo/tool")
    a = ap.parse_args(argv)
    maps = {}
    for m in a.map:
        k, v = m.split("=", 1)
        maps[k] = os.path.join(ROOT, v)
    w, h = (int(x) for x in a.size.lower().split("x"))
    out = a.out or os.path.join(ROOT, "qa", "sources", a.repo)
    rep = run(a.repo, a.page, a.ready, a.draw, [float(x) for x in a.t.split(",")], (w, h), out, maps, wait=a.wait)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
