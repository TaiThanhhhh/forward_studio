"""Kiểm thử đầu-cuối QUA UI (Phần C): Projects → Script → Board → Generate → Edit → Review → Deliver.

  python scripts/ui_e2e.py [--only glass,xray,swarm,flat] [--real-tts flat] [--rerender-only]

Playwright (Edge headless) bấm/gõ trên UI như người làm; CLI không được gọi trực tiếp. Bước "viết storyboard" đóng vai
/video trong Claude Code (LLM viết storyboard từ brief) — ghi storyboard.json rồi quay lại UI. Clip Flow là clip GIẢ
(ffmpeg testsrc2) tải lên qua trang Generate (kiểm tự map theo tên). Ghi: qa/ui/after/*.png, qa/ui/e2e.json.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vidlib import storyboard as sbm  # noqa: E402
from vidlib.common import PROJECTS, ffbin, load_json  # noqa: E402

PORT = 8794
BASE = f"http://127.0.0.1:{PORT}"
IDEA = "What happens if you drop a 1,000°C steel ball into ice water?"
OUT = os.path.join(ROOT, "qa", "ui", "after")
CASES = {  # key: (style, nhãn để phân biệt slug, loại)
    "glass": ("atlas-glass-and-light", "atlas glass test", "hybrid"),
    "xray": ("atlas-x-ray", "atlas xray test", "three"),
    "swarm": ("atlas-particle-swarm", "atlas swarm test", "three"),
    "flat": ("flat-vector-black", "classic flat test", "html"),
}
VO = [("hook", "[excited] Drop a thousand-degree steel ball into ice water."),
      ("setup", "It glows orange, as hot as fresh lava."),
      ("escalate", "The water touching it flashes into steam instantly."),
      ("escalate", "That steam wraps the ball in a shield, so the water can't touch it."),
      ("payoff", "The ball keeps glowing underwater for seconds."),
      ("twist", "Then the shield collapses, and the water boils violently.")]


def stage(props, fx=None, frame=None):
    p = {"props": props}
    if fx:
        p["fx"] = fx
    if frame:
        p["frame"] = frame
    return {"scene": "stage", "params": p}


BALL = {"id": "ball", "type": "ball", "r": 0.12}
BEAKER = {"id": "beaker", "type": "beaker", "at": [0, 0, 0], "r": 0.22, "h": 0.46, "water": 0.72}


def code_shots():
    return [
        stage([{**BEAKER}, {**BALL, "hot": 1, "keys": [{"u": 0, "at": [0, 1.15, 0]}, {"u": 1, "at": [0, 0.62, 0], "ease": "easeIn"}]},
               {"id": "ice", "type": "ice", "at": [0.3, 0.05, 0.16]}]),
        stage([{**BALL, "at": [-0.25, 0.45, 0], "hot": 1}, {"id": "th", "type": "thermometer", "at": [0.32, 0.1, 0], "value": 1000, "lo": 0, "hi": 1200,
               "keys": [{"u": 0, "value": 20}, {"u": 1, "value": 1000, "ease": "easeOut"}]}]),
        stage([{**BEAKER}, {**BALL, "at": [0, 0.22, 0], "hot": 0.95}], fx=[{"kind": "steam", "of": "beaker", "u": [0, 1], "r": 0.25},
                                                                           {"kind": "bubbles", "of": "ball", "u": [0.1, 1], "r": 0.16}]),
        stage([{**BEAKER}, {**BALL, "at": [0, 0.22, 0], "hot": 0.9}], fx=[{"kind": "shockwave", "of": "ball", "u": [0.05, 0.6], "r": 0.22},
                                                                          {"kind": "steam", "of": "ball", "u": [0, 1], "r": 0.18}]),
        stage([{**BEAKER}, {**BALL, "at": [0, 0.22, 0], "keys": [{"u": 0, "hot": 0.9}, {"u": 1, "hot": 0.6}]}],
              fx=[{"kind": "bubbles", "of": "ball", "u": [0, 1], "r": 0.12}]),
        stage([{**BEAKER}, {**BALL, "at": [0, 0.22, 0], "keys": [{"u": 0, "hot": 0.5}, {"u": 1, "hot": 0.05}]}],
              fx=[{"kind": "burst", "of": "ball", "u": [0.1, 0.5], "r": 0.3}, {"kind": "splash", "of": "beaker", "u": [0.2, 0.7], "r": 0.3},
                  {"kind": "steam", "of": "beaker", "u": [0.15, 1], "r": 0.3}]),
    ]


def html_shots():
    return [
        {"scene": "drop", "params": {"title": "Drop it in", "a": {"icon": "ball", "label": "1,000°C steel", "role": "hot"},
                                     "b": {"icon": "glass", "label": "ice water"}, "result": "Instant steam", "hit": 0.45, "sfx": "splash"}},
        {"scene": "counter", "params": {"title": "Surface heat", "from": 20, "to": 1000, "suffix": "°C", "unit": "glowing orange", "icon": "flame"}},
        {"scene": "compare", "params": {"title": "Who wins?", "left": {"icon": "ball", "icon_role": "hot", "label": "Steel ball", "value": 1000, "unit": "°C"},
                                        "right": {"icon": "ice", "label": "Ice water", "value": 0, "unit": "°C"}, "vs": "VS", "result": "Steam first"}},
        {"scene": "fact", "params": {"kicker": "the twist", "text": "The water never touches the steel", "em": "at first"}},
        {"scene": "process", "params": {"title": "Leidenfrost effect", "steps": [{"icon": "ball", "role": "hot", "label": "Steel hits water"},
                                        {"icon": "steam", "label": "Vapor shield forms"}, {"icon": "bubble", "label": "Shield collapses"},
                                        {"icon": "snow", "label": "Violent boiling"}]}},
        {"scene": "fact", "params": {"kicker": "result", "text": "Then the water boils violently", "em": "violently"}},
    ]


FLOW_DESC = {
    0: ("A glowing orange-hot steel ball hangs above a clear glass of ice water", "the ball drops straight down into the water"),
    2: ("The glowing steel ball sits in the water while a thick column of white steam erupts upward", "steam keeps erupting and swirling upward"),
    5: ("The dimmed steel ball rests in the water as large bubbles burst violently around it", "the water churns and bubbles burst all around the ball"),
}


def storyboard(case, slug, plan):
    style, _, kind = CASES[case]
    shots = []
    codes = html_shots() if kind == "html" else code_shots()
    for i, (beat, vo) in enumerate(VO):
        s = {"id": f"C{i + 1:02d}", "beat": beat, "vo": vo, "target_sec": 2.6, "camera": "", "subject": "a glowing steel ball and a glass of ice water",
             "start_frame": {"desc": ""}, "end_frame": {"desc": ""}, "action": []}
        if kind == "hybrid" and i in FLOW_DESC:
            d, a = FLOW_DESC[i]
            s.update({"mode": "frames_start", "start_frame": {"desc": d}, "action": [{"do": a, "t": [0, 3]}], "camera": "Slow push-in",
                      "accent_on": "the glowing ball"})
        else:
            s.update({"mode": "code", "code": codes[i]})
        if i == 1:
            s["text_fx"] = [{"text": "1,000°C", "anchor": "world_xy", "pos": [0.5, 0.2], "behavior": ["pop_from", "settle"], "role": "main",
                             "sync": "vo_word:orange"}]
        shots.append(s)
    return {"slug": slug, "topic": IDEA, "title": "1,000°C Steel Ball vs Ice Water", "hook": "A thousand-degree ball goes into ice water, and the water can't touch it.",
            "truth": "True", "experiment_no": 1, "style": style, "voice": "auto", "narrative": plan.get("narrative") or "classic", "language": "en",
            "shots": shots,
            "outro": {"teaser": "Molten salt vs water?", "mode": "code", "enabled": True, "loop": True, "follow_text": "Follow for the next experiment"},
            "thumbnail": {"variants": [{"id": "T1", "archetype": "before_disaster", "text": "1,000°C vs ICE", "scene": "a glowing steel ball above ice water"},
                                       {"id": "T2", "archetype": "red_circle", "text": "WATER CAN'T TOUCH IT", "scene": "the ball wrapped in steam underwater"}]},
            "publish": {"titles": ["1,000°C Steel Ball vs Ice Water", "Why Water Can't Touch Red-Hot Steel", "The Leidenfrost Shield, Explained"],
                        "description": "A red-hot steel ball wraps itself in a shield of steam when it hits ice water. Then the shield collapses and the water boils violently.",
                        "hashtags": ["leidenfrost", "physics", "science", "experiment", "steel", "shorts"]},
            "sources": [{"title": "Leidenfrost effect", "url": "https://en.wikipedia.org/wiki/Leidenfrost_effect"}]}


def fake_clip(path, sec=5):
    if os.path.exists(path):
        return path
    subprocess.run([ffbin("ffmpeg"), "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size=720x1280:rate=24:duration={sec}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", path], check=True)
    return path


def api(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.load(r)


def wait_jobs(slug, timeout=1800, label=""):
    t0 = time.time()
    last = None
    time.sleep(1.0)
    while time.time() - t0 < timeout:
        items = [j for j in api("/api/jobs")["items"] if j.get("slug") == slug or (label and label in (j.get("title") or ""))]
        if items:
            last = items[0]
            if not any(j["status"] in ("running", "queued") for j in items):
                return last
        time.sleep(2)
    raise TimeoutError(f"job {slug} quá {timeout}s")


class Clicks:
    def __init__(self, pg):
        self.pg, self.n, self.screens, self.log = pg, 0, set(), []

    def click(self, sel, **kw):
        self.pg.locator(sel).first.click(**kw)
        self.n += 1
        self.log.append(sel)

    def key(self, k):
        self.pg.keyboard.press(k)
        self.n += 1

    def screen(self):
        self.screens.add(self.pg.evaluate("location.hash.split('/').slice(0, 4).join('/').replace(/p\\/[^/]+/, 'p')"))

    def reset(self):
        n, s = self.n, len(self.screens)
        self.n, self.screens, self.log = 0, set(), []
        return {"clicks": n, "screens": s}


def shot(pg, name, sizes=((1440, 900),)):
    os.makedirs(OUT, exist_ok=True)
    for w, h in sizes:
        pg.set_viewport_size({"width": w, "height": h})
        pg.wait_for_timeout(400)
        pg.screenshot(path=os.path.join(OUT, f"{w}x{h}_{name}.png"))
    pg.set_viewport_size({"width": 1440, "height": 900})


def run_case(pg, case, real_tts, results, first):
    style, tag, kind = CASES[case]
    idea = f"{tag.capitalize()}: {IDEA}"   # nhãn ĐẦU câu: slugify cắt ngắn nên nhãn cuối câu làm trùng slug
    slug = sbm_slug(idea)
    c = Clicks(pg)
    R = results.setdefault(case, {"style": style, "slug": slug, "tasks": {}})
    # ---- tác vụ 1: tạo video từ ý tưởng (Projects)
    pg.goto(f"{BASE}/#/projects")
    pg.wait_for_timeout(1200)
    c.screen()
    pg.fill("#new-idea", idea)
    c.click("summary:has-text('Nâng cao')")
    pg.select_option("select[aria-label='Style']", style)
    # đặt trạng thái TƯỜNG MINH: UI nhớ lựa chọn lần trước → bấm đảo có thể tắt chạy thử (lần swarm đã lỡ gọi ElevenLabs thật)
    box = pg.locator("label.check:has-text('Chạy thử') input")
    if box.is_checked() == real_tts:
        c.click("label.check:has-text('Chạy thử')")
    assert box.is_checked() != real_tts, "ô Chạy thử sai trạng thái"
    if first:
        shot(pg, "projects", ((1440, 900), (1920, 1080)))
    c.click("button:has-text('Tạo video')")
    job = wait_jobs(slug)
    R["create_job"] = {"stage": job.get("stage"), "exit": job.get("exit_code")}
    pg.wait_for_timeout(1500)
    c.screen()
    R["tasks"]["1_create"] = c.reset()
    # ---- bước /video: LLM viết storyboard từ brief (ở đây: storyboard mẫu cố định của bài kiểm)
    proj = os.path.join(PROJECTS, slug)
    plan = load_json(os.path.join(proj, "plan.json"), {}) or {}
    sbm.save(proj, storyboard(case, slug, plan))
    # ---- Script → Chạy tiếp (prompt, trang, …)
    pg.goto(f"{BASE}/#/p/{slug}/script")
    pg.wait_for_timeout(1500)
    if first:
        shot(pg, "script", ((1440, 900), (1920, 1080)))
    if kind == "hybrid":
        # ---- tác vụ 2: Generate — bảng sản xuất Flow + thả clip (tự map theo tên)
        c.click("button:has-text('Chạy tiếp')")      # prompts + trang → dừng chờ clip (hoặc chạy hết nếu dry-run)
        wait_jobs(slug)
        pg.goto(f"{BASE}/#/p/{slug}/generate")
        pg.wait_for_timeout(1800)
        c.screen()
        shot(pg, "generate", ((1440, 900), (1920, 1080)))
        clips_dir = os.path.join(ROOT, "qa", "ui", "_fake_clips")
        os.makedirs(clips_dir, exist_ok=True)
        files = [fake_clip(os.path.join(clips_dir, f"flow_C{i + 1:02d}_take1.mp4")) for i in FLOW_DESC]
        pg.locator("input[type=file]").set_input_files(files)
        c.n += 1
        pg.wait_for_timeout(800)
        c.click(".modal button:has-text('Tải lên')")
        pg.wait_for_timeout(4000)
        c.click("button:has-text('Chạy tiếp')")
        job = wait_jobs(slug)
        R["tasks"]["2_flow"] = c.reset()
    else:
        c.click("button:has-text('Chạy tiếp')")
        job = wait_jobs(slug)
    R["render_job"] = {"stage": job.get("stage"), "exit": job.get("exit_code")}
    # ---- Board
    pg.goto(f"{BASE}/#/p/{slug}/board")
    pg.wait_for_timeout(1500)
    if first or kind == "hybrid":
        shot(pg, f"board_{case}", ((1440, 900),))
    # ---- tác vụ 3: sửa một shot rồi render lại riêng shot đó (Edit)
    pg.goto(f"{BASE}/#/p/{slug}/edit")
    pg.wait_for_timeout(2000)
    c.screen()
    if first:
        shot(pg, "edit", ((1440, 900), (1920, 1080)))
    task_rerender(pg, c, slug, R)
    # ---- tác vụ 4: review + comment (Review)
    pg.goto(f"{BASE}/#/p/{slug}/review")
    pg.wait_for_timeout(2000)
    c.screen()
    pg.evaluate("document.querySelector('video').currentTime = 3.2")
    pg.wait_for_timeout(500)
    c.key("D")
    box = pg.locator("canvas.ink").bounding_box()
    if box:
        pg.mouse.move(box["x"] + box["width"] * 0.4, box["y"] + box["height"] * 0.45)
        pg.mouse.down()
        for k in range(12):
            pg.mouse.move(box["x"] + box["width"] * (0.4 + 0.02 * k), box["y"] + box["height"] * (0.45 + (0.01 * (k % 4))))
        pg.mouse.up()
        c.n += 1
    pg.fill("textarea[aria-label='Nội dung comment']", "Steam starts one frame late here — check the C03 cut.")
    c.click("button:has-text('Thêm comment')")
    pg.wait_for_timeout(800)
    c.click("button:has-text('Duyệt')")
    pg.wait_for_timeout(800)
    if first:
        shot(pg, "review", ((1440, 900), (1920, 1080)))
    R["tasks"]["4_review"] = c.reset()
    R["review"] = api(f"/api/v2/projects/{slug}/review")
    # ---- tác vụ 5: xuất bản Shorts / Reels / TikTok (Deliver)
    pg.goto(f"{BASE}/#/p/{slug}/deliver")
    pg.wait_for_timeout(1800)
    c.screen()
    btn = pg.locator("button:has-text('Xuất gói')").first
    if btn.is_enabled():
        c.click("button:has-text('Xuất gói')")
        wait_jobs(slug)
        pg.wait_for_timeout(2500)
    R["deliver_enabled"] = btn.is_enabled()
    shot(pg, f"deliver_{case}", ((1440, 900), (1920, 1080)) if first else ((1440, 900),))
    R["tasks"]["5_deliver"] = c.reset()
    ws = api(f"/api/v2/projects/{slug}/workspace")
    R["qa"] = ws.get("qa", {}).get("gate")
    R["deliver"] = {k: v["verdict"] for k, v in (ws.get("deliver") or {}).items()}
    R["version"] = (ws.get("manifest") or {}).get("version")
    if first:
        pg.goto(f"{BASE}/#/library")
        pg.wait_for_timeout(1500)
        shot(pg, "library", ((1440, 900), (1920, 1080)))
        pg.goto(f"{BASE}/#/_design")
        pg.wait_for_timeout(800)
        shot(pg, "design", ((1440, 900),))
    return R


def task_rerender(pg, c, slug, R, target="C02"):
    """Tác vụ 3 (đang ở trang Edit): chọn shot trên timeline → Render lại shot → xác nhận → chờ job."""
    c.click(f".tl .clip[data-id='{target}']")
    c.click("button:has-text('Render lại shot')")
    c.click(".modal button:has-text('Render lại')")
    job = wait_jobs(slug)
    R["tasks"]["3_rerender"] = c.reset()
    R["rerender_job"] = {"stage": job.get("stage"), "exit": job.get("exit_code")}


def rerender_case(pg, case, results):
    """--rerender-only: chạy lại riêng tác vụ 3 trên dự án đã có (giữ kết quả các tác vụ khác)."""
    R = results[case]
    pg.goto(f"{BASE}/#/p/{R['slug']}/edit")
    pg.wait_for_timeout(2000)
    c = Clicks(pg)
    c.screen()
    task_rerender(pg, c, R["slug"], R)
    ws = api(f"/api/v2/projects/{R['slug']}/workspace")
    R["qa"] = ws.get("qa", {}).get("gate")
    R["version"] = (ws.get("manifest") or {}).get("version")
    return R


def sbm_slug(idea):
    from vidlib.common import slugify  # noqa: PLC0415
    return slugify(idea)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--real-tts", default="")
    ap.add_argument("--rerender-only", action="store_true", help="chỉ chạy lại tác vụ 3 trên dự án đã có")
    a = ap.parse_args(argv)
    cases = a.only.split(",") if a.only else list(CASES)
    srv = subprocess.Popen([sys.executable, "-m", "ui.server", "--port", str(PORT), "--no-open"], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    results = load_json(os.path.join(ROOT, "qa", "ui", "e2e.json"), {}) or {}
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(BASE + "/", timeout=1)
                break
            except OSError:
                time.sleep(0.25)
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge", headless=True)
            ctxb = b.new_context(viewport={"width": 1440, "height": 900})
            pg = ctxb.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            for i, case in enumerate(cases):
                t0 = time.time()
                print(f"▶ {case} · {CASES[case][0]}", flush=True)
                try:
                    if a.rerender_only:
                        results[case].pop("error", None)
                        rerender_case(pg, case, results)
                    else:
                        run_case(pg, case, case in a.real_tts.split(","), results, first=(i == 0))
                except Exception as e:  # noqa: BLE001
                    results.setdefault(case, {})["error"] = repr(e)[:400]
                    pg.screenshot(path=os.path.join(OUT, f"error_{case}.png"))
                results[case]["sec"] = round(time.time() - t0)
                results[case]["page_errors"] = errs[:]
                errs.clear()
                with open(os.path.join(ROOT, "qa", "ui", "e2e.json"), "w", encoding="utf-8") as fh:
                    json.dump(results, fh, ensure_ascii=False, indent=1)
                r = results[case]
                print(f"  {case}: render {r.get('render_job')} · rerender {r.get('rerender_job')} · deliver {r.get('deliver')} · "
                      f"{r.get('sec')}s · tasks {r.get('tasks')}" + (f" · LỖI {r['error']}" if r.get("error") else ""), flush=True)
            b.close()
    finally:
        srv.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
