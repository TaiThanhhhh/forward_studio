"""Kiểm UI tự động: axe-core (WCAG 2 A/AA) trên mọi trang + đo chuyển trang và mở video Review.

  python scripts/ui_check.py --axe <đường dẫn axe.min.js> [--slug <dự án>] [--out qa/ui/check.json]

axe.min.js (MPL-2.0) KHÔNG nằm trong repo — tải riêng (cdnjs axe-core) rồi truyền đường dẫn.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8795
PAGES = ["/projects", "/p/{slug}/script", "/p/{slug}/board", "/p/{slug}/generate", "/p/{slug}/edit", "/p/{slug}/review",
         "/p/{slug}/deliver", "/library", "/library/voices", "/library/rights", "/_design"]


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--axe", required=True)
    ap.add_argument("--slug", default="steel-ball-1000c-ice-water")
    ap.add_argument("--out", default=os.path.join(ROOT, "qa", "ui", "check.json"))
    a = ap.parse_args(argv)
    axe = open(a.axe, encoding="utf-8").read()
    srv = subprocess.Popen([sys.executable, "-m", "ui.server", "--port", str(PORT), "--no-open"], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = {"axe": {}, "perf": {}}
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1)
                break
            except OSError:
                time.sleep(0.25)
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge", headless=True)
            pg = b.new_page(viewport={"width": 1440, "height": 900})
            base = f"http://127.0.0.1:{PORT}/#"
            for r in PAGES:
                path = r.format(slug=a.slug)
                pg.goto(base + path)
                pg.wait_for_timeout(1500)
                pg.evaluate(axe)
                v = pg.evaluate("""async () => { const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } });
                  return r.violations.map(v => ({ id: v.id, impact: v.impact, help: v.help, n: v.nodes.length, target: v.nodes.slice(0, 3).map(n => n.target.join(' ')) })); }""")
                res["axe"][path] = v
                bad = [x for x in v if x["impact"] in ("serious", "critical")]
                print(f"  axe {path:<34} {len(v)} vi phạm · {len(bad)} serious/critical " + ", ".join(f"{x['id']}×{x['n']}" for x in bad))
            # chuyển trang (đã có cache workspace): thời gian tới khi nội dung trang mới gắn vào DOM
            pg.goto(base + f"/p/{a.slug}/board")
            pg.wait_for_timeout(1500)
            times = []
            for nxt in ["script", "board", "generate", "edit", "deliver", "board"]:
                ms = pg.evaluate("""(h) => new Promise((res) => { const host = document.querySelector('main.main > div');
                  const t0 = performance.now(); const ob = new MutationObserver(() => { ob.disconnect(); res(performance.now() - t0); });
                  ob.observe(host, { childList: true }); location.hash = h; setTimeout(() => res(-1), 5000); })""", f"#/p/{a.slug}/{nxt}")
                times.append(round(ms, 1))
                pg.wait_for_timeout(600)
            res["perf"]["page_switch_ms"] = times
            # mở video Review: từ lúc vào trang tới loadeddata
            pg.goto(base + f"/p/{a.slug}/board")
            pg.wait_for_timeout(1000)
            ms = pg.evaluate("""(h) => new Promise((res) => { const t0 = performance.now(); location.hash = h;
              const poll = () => { const v = document.querySelector('video'); if (v) { if (v.readyState >= 2) return res(performance.now() - t0);
                v.addEventListener('loadeddata', () => res(performance.now() - t0), { once: true }); } else setTimeout(poll, 10); }; poll();
              setTimeout(() => res(-1), 8000); })""", f"#/p/{a.slug}/review")
            res["perf"]["review_video_ms"] = round(ms, 1)
            print(f"  chuyển trang (ms): {times} · mở video Review: {round(ms)} ms")
            b.close()
    finally:
        srv.terminate()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    serious = sum(1 for v in res["axe"].values() for x in v if x["impact"] in ("serious", "critical"))
    print(f"  → serious/critical: {serious}")
    return 1 if serious else 0


if __name__ == "__main__":
    sys.exit(main())
