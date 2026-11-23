"""Chụp mọi màn hình UI bằng Playwright (Edge/Chromium headless) — dùng cho audit UI và so trước/sau.

  python scripts/ui_shots.py <thư mục ra> [--size 1440x900,1920x1080] [--routes a,b] [--slug <dự án mẫu>]

Tự bật server UI tạm (cổng 8797, không mở trình duyệt), chụp từng route, ghi console error vào errors.json, rồi tắt.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8797
NEW_ROUTES = ["/projects", "/p/{slug}/script", "/p/{slug}/board", "/p/{slug}/generate", "/p/{slug}/edit", "/p/{slug}/review",
              "/p/{slug}/deliver", "/library", "/library/voices", "/library/rights", "/_design"]
OLD_ROUTES = ["/", "/new", "/projects", "/projects/{slug}", "/projects/{slug}?tab=shots", "/projects/{slug}?tab=outputs",
              "/projects/{slug}?tab=qa", "/ideas", "/jobs", "/library/styles", "/library/voices", "/library/narratives",
              "/settings"]


def wait_up(url, sec=20):
    t0 = time.time()
    while time.time() - t0 < sec:
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return True
        except OSError:
            time.sleep(0.3)
    return False


def shoot(out, routes, sizes, slug, settle=1.2, actions=None):
    from playwright.sync_api import sync_playwright  # noqa: PLC0415
    os.makedirs(out, exist_ok=True)
    srv = subprocess.Popen([sys.executable, "-m", "ui.server", "--port", str(PORT), "--no-open"], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors = {}
    shots = []
    try:
        if not wait_up(f"http://127.0.0.1:{PORT}/"):
            raise SystemExit("server UI không lên")
        with sync_playwright() as p:
            try:
                b = p.chromium.launch(channel="msedge", headless=True)
            except Exception:  # noqa: BLE001
                b = p.chromium.launch(headless=True)
            for w, h in sizes:
                pg = b.new_page(viewport={"width": w, "height": h})
                pg.on("console", lambda m, pg=pg: m.type == "error" and errors.setdefault(pg.url, []).append(m.text))
                pg.on("pageerror", lambda e, pg=pg: errors.setdefault(pg.url, []).append(str(e)))
                for r in routes:
                    path = r.format(slug=slug)
                    pg.goto(f"http://127.0.0.1:{PORT}/#{path}")
                    pg.wait_for_timeout(int(settle * 1000))
                    name = (path.strip("/").replace("/", "_").replace("?", "_").replace("=", "-") or "home")
                    name = name.replace(slug, "P")
                    f = os.path.join(out, f"{w}x{h}_{name}.png")
                    pg.screenshot(path=f, full_page=False)
                    shots.append(f)
                    for act in (actions or {}).get(r, []):
                        act(pg)
                pg.close()
            b.close()
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except subprocess.TimeoutExpired:
            srv.kill()
    with open(os.path.join(out, "errors.json"), "w", encoding="utf-8") as fh:
        json.dump(errors, fh, ensure_ascii=False, indent=1)
    return shots, errors


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--size", default="1440x900")
    ap.add_argument("--routes")
    ap.add_argument("--slug", default="steel-ball-1000c-ice-water")
    a = ap.parse_args(argv)
    sizes = [tuple(int(x) for x in s.split("x")) for s in a.size.split(",")]
    routes = a.routes.split(",") if a.routes and a.routes not in ("new", "old") else (OLD_ROUTES if a.routes == "old" else NEW_ROUTES)
    shots, errors = shoot(os.path.join(ROOT, a.out) if not os.path.isabs(a.out) else a.out, routes, sizes, a.slug)
    print(f"{len(shots)} ảnh · lỗi console ở {len(errors)} trang")
    return 0


if __name__ == "__main__":
    sys.exit(main())
