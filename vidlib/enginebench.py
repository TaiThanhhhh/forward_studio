"""Vòng 7: benchmark engine html / manim (+ HyperFrames để quyết định có thay harness hay không) và gallery style.

python studio.py perf engines        → docs/perf_engines.json + mục 3–4 của docs/PERF.md
python studio.py styles --gallery    → qa/styles/<id>.jpg + qa/styles-gallery.png (mỗi style một style frame 9:16)
"""

import datetime
import json
import os
import shutil
import subprocess
import time

from engines import adapter

from . import textstyle
from .common import ROOT, load_json

TEST = os.path.join(ROOT, "projects", "_engine_test")
HF_DIR = os.path.join(ROOT, "vendor", "_hf_run")


def demo():
    return load_json(os.path.join(ROOT, "engines", "html", "demo.json"))


def _spec(engine, beat, style, frames, tag):
    return adapter.ShotSpec(
        sid=tag,
        engine=engine,
        scene=beat,
        params=demo()[beat],
        frames=frames,
        style=style,
        work=os.path.join(TEST, "work", "code", tag),
    )


def bench_html(frames=90, beat="drop", style="hud-black", workers=(1, 2, 4, 6, 8)):
    eng = adapter.get("html")
    spec = _spec("html", beat, style, frames, "PERF_HTML")
    job = eng.job(spec)
    rows = []
    for w in workers:
        out = os.path.join(spec.work, f"bench_{w}")
        shutil.rmtree(out, ignore_errors=True)
        st = eng.render(job, out, None, log=lambda m: None, workers=w)
        rows.append({"workers": w, **st})
        shutil.rmtree(out, ignore_errors=True)
    return {"beat": beat, "style": style, "frames": frames, "rows": rows}


def bench_manim(frames=90, beat="graph", style="physics-diagram-black"):
    eng = adapter.get("manim")
    spec = _spec("manim", beat, style, frames, "PERF_MANIM")
    job = eng.job(spec)
    shutil.rmtree(os.path.join(spec.work, "frames"), ignore_errors=True)
    return {
        "beat": beat,
        "style": style,
        "frames": frames,
        **eng.render(job, os.path.join(spec.work, "frames"), log=lambda m: None),
    }


def bench_hyperframes(frames=90, beat="drop", style="hud-black"):
    """CÙNG nội dung (trang engine html của tool) nhưng để HyperFrames chụp frame + mã hoá — so harness với harness.
    Cần vendor/_hf_run (npm install hyperframes --ignore-scripts). Không có → None."""
    cli = os.path.join(HF_DIR, "node_modules", "hyperframes")
    if not os.path.isdir(cli) or not shutil.which("node"):
        return None
    eng = adapter.get("html")
    spec = _spec("html", beat, style, frames, "PERF_HTML")
    job = adapter.load_job(eng.job(spec))
    comp = os.path.join(HF_DIR, "bench")
    shutil.rmtree(comp, ignore_errors=True)
    for sub in ("engines/html", "lib/motion", "assets/fonts"):
        os.makedirs(os.path.join(comp, os.path.dirname(sub)), exist_ok=True)
    shutil.copytree(
        os.path.join(ROOT, "engines", "html"),
        os.path.join(comp, "engines", "html"),
        ignore=shutil.ignore_patterns("__pycache__", "*.py"),
    )
    shutil.copytree(
        os.path.join(ROOT, "lib", "motion"),
        os.path.join(comp, "lib", "motion"),
        ignore=shutil.ignore_patterns("__pycache__", "*.py"),
    )
    os.makedirs(os.path.join(comp, "assets", "fonts"), exist_ok=True)
    for f in job["fonts"]:
        shutil.copy(os.path.join(ROOT, "assets", "fonts", f["file"]), os.path.join(comp, "assets", "fonts", f["file"]))
    with open(os.path.join(comp, "job.json"), "w", encoding="utf-8") as fh:
        json.dump(job, fh)
    gsap = next(
        (
            os.path.join(dp, "gsap.min.js")
            for dp, _, fn in os.walk(os.path.join(HF_DIR, "node_modules"))
            if "gsap.min.js" in fn
        ),
        None,
    )
    if gsap:
        shutil.copy(gsap, os.path.join(comp, "gsap.min.js"))
    dur = frames / job["fps"]
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<script src="{"gsap.min.js" if gsap else "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"}"></script>
<style>html,body{{margin:0;background:#000;width:{job["width"]}px;height:{job["height"]}px;overflow:hidden}}canvas{{display:block}}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{job["width"]}" data-height="{job["height"]}" data-fps="{job["fps"]}">
<canvas id="c" width="{job["width"]}" height="{job["height"]}"></canvas></div>
<script>
  // HyperFrames tua timeline GSAP; mỗi lần tua gọi đúng hàm vẽ frame của engine html (cùng nội dung với harness của tool).
  history.replaceState(null, "", location.pathname + "?job=job.json");
  const st = {{ f: 0 }};
  window.__timelines = window.__timelines || {{}};
  window.__timelines["main"] = gsap.timeline({{ paused: true }}).to(st, {{ f: {frames - 1}, duration: {dur}, ease: "none",
    onUpdate: () => {{ if (window.renderFrame) window.renderFrame(Math.round(st.f)); }} }});
</script>
<script type="module" src="engines/html/core.js"></script></body></html>"""
    with open(os.path.join(comp, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    from .common import ffbin  # noqa: PLC0415

    env = {
        **os.environ,
        "HYPERFRAMES_NO_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "HYPERFRAMES_NO_UPDATE_CHECK": "1",
        "HYPERFRAMES_CACHE_DIR": os.path.join(HF_DIR, "cache"),
        "HYPERFRAMES_FFMPEG_PATH": ffbin("ffmpeg"),
    }
    for cand in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ):
        if os.path.exists(cand):
            env["HYPERFRAMES_BROWSER_PATH"] = cand
            break
    out = os.path.join(HF_DIR, "out", "bench.mp4")
    t0 = time.time()
    pr = subprocess.run(
        ["node", os.path.join(cli, "bin", "hyperframes.mjs"), "render", comp, "-o", out],
        cwd=HF_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    dt = time.time() - t0
    log = pr.stdout + pr.stderr
    ok = pr.returncode == 0 and os.path.exists(out)
    cap = None
    for part in log.split("·"):
        if part.strip().startswith("capture "):
            cap = float(part.strip().split()[1].rstrip("s"))
    wk = None
    if "workers)" in log:
        wk = int(log.split("workers)")[0].rsplit("(", 1)[1].split()[0])
    return {
        "ok": ok,
        "frames": frames,
        "total_sec": round(dt, 2),
        "capture_sec": cap,
        "workers": wk,
        "sec_per_frame_total": round(dt / frames, 3),
        "sec_per_frame_capture": round(cap / frames, 3) if cap else None,
        "version": load_json(os.path.join(cli, "package.json"), {}).get("version"),
        "error": None if ok else log[-400:],
    }


def perf_engines(frames=90):
    from .tools import _cpu, write_perf_md  # noqa: PLC0415

    data = {
        "meta": {"date": f"{datetime.date.today():%d/%m/%Y}", "cpu": _cpu(), "cores": os.cpu_count() or 2, "frames": frames},
        "html": bench_html(frames),
        "manim": bench_manim(frames),
        "hyperframes": bench_hyperframes(frames),
    }
    with open(os.path.join(ROOT, "docs", "perf_engines.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return write_perf_md()


def perf_section():
    """Dòng Markdown cho docs/PERF.md (mục 3–4) từ docs/perf_engines.json."""
    p = os.path.join(ROOT, "docs", "perf_engines.json")
    if not os.path.exists(p):
        return []
    d = load_json(p)
    m, h, mn, hf = d["meta"], d["html"], d["manim"], d.get("hyperframes")
    best = min(h["rows"], key=lambda r: r["sec_per_frame"])
    L = [
        "## 3. Engine html (engines/html/, Canvas 2D trong Edge headless) và engine manim",
        "",
        f"Đo ngày {m['date']} bằng `python studio.py perf engines` · {m['frames']} frame 1080×1920 · beat `{h['beat']}` · style `{h['style']}` "
        f"· {m['cpu']} ({m['cores']} luồng).",
        "",
        "| Engine | Worker | Tổng (s) | s/frame (wall) |",
        "|---|---|---|---|",
    ]
    L += [
        f"| html (harness của tool: Playwright + Edge) | {r['workers']} | {r['sec']} | {r['sec_per_frame']} |"
        for r in h["rows"]
    ]
    L += [
        f"| manim CE (Cairo, 1 tiến trình; beat `{mn['beat']}`) | 1 | {mn['sec']} | {mn['sec_per_frame']} |",
        "",
        f"- html nhanh nhất: {best['workers']} worker → **{best['sec_per_frame']} s/frame**. Canvas 2D chạy trên CPU của tiến trình "
        "trình duyệt, nhưng shot ngắn (60–150 frame) thì thời gian mở trình duyệt chiếm phần lớn → ít worker nhanh hơn. "
          "Mặc định `code_render.html_workers = 0` (= 2, theo số đo).",
        "- manim chậm hơn hẳn (dựng lại chữ mỗi frame) → chỉ dùng cho shot sơ đồ (đồ thị, vector, phương trình).",
        "",
    ]
    L += ["## 4. Có thay harness render bằng HyperFrames không?", ""]
    if not hf:
        L += ["- Chưa đo (không có `vendor/_hf_run`).", ""]
    elif not hf.get("ok"):
        L += [
            f"- HyperFrames {hf.get('version')} không dựng được trang của engine html: `{(hf.get('error') or '')[-200:]}`",
            "",
        ]
    else:
        L += [
            f"Cùng nội dung ({m['frames']} frame của engine html), HyperFrames {hf['version']} chụp + mã hoá:",
            "",
            "| Harness | Worker | Tổng (s) | s/frame (tổng) | s/frame (riêng bước chụp) |",
            "|---|---|---|---|---|",
            f"| Harness của tool (Playwright, JPEG từ canvas) | {best['workers']} | {best['sec']} | {best['sec_per_frame']} | {best['sec_per_frame']} |",
            f"| HyperFrames (Node + Chrome, screenshot) | {hf['workers']} | {hf['total_sec']} | {hf['sec_per_frame_total']} | {hf['sec_per_frame_capture']} |",
            "",
        ]
        faster = hf["sec_per_frame_total"] <= best["sec_per_frame"]
        L += [
            f"- **Quyết định: {'chuyển sang HyperFrames' if faster else 'GIỮ harness của tool'}** — HyperFrames "
            f"{'nhanh hơn hoặc bằng' if faster else 'chậm hơn'} trên cùng nội dung"
            + (
                ""
                if faster
                else "; ngoài ra nó cần Node ≥ 22 lúc chạy (tool hiện không cần Node), ~120 MB node_modules, mặc định bật "
                "telemetry và tải GSAP/font từ CDN lúc render, và không có RESUME theo frame."
            )
            + "",
            "- Giá trị giữ lại từ HyperFrames: hợp đồng 'trang tua được theo thời gian' (engine html dùng cùng ý tưởng) và catalog "
            "component để tham khảo khi viết beat mới (`vendor/hyperframes/registry`).",
            "",
        ]
    return L


# ---------------------------------------------------------------------------------------------------------------------
def style_frame(style, out):
    """Một style frame 9:16 của style → out (.jpg). html/manim: frame thật của engine; còn lại: thẻ chữ theo kiểu chữ của style."""
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    st = textstyle.load_style(style)
    eng = st.get("code_engine")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if eng in ("html", "manim"):
        beat = (
            "graph"
            if eng == "manim"
            else (
                "scale"
                if st.get("html", {}).get("look") == "zoom"
                else "process"
                if st.get("html", {}).get("look") in ("flow", "picto")
                else "drop"
            )
        )
        n = 60
        spec = adapter.ShotSpec(
            sid=style,
            engine=eng,
            scene=beat,
            params=demo()[beat],
            frames=n,
            style=style,
            index=[3, 7],
            work=os.path.join(ROOT, "qa", "styles", "_work", style),
        )
        e = adapter.get(eng)
        job = e.job(spec)
        f = n - 1 if beat != "scale" else 2
        e.render(job, os.path.join(spec.work, "frames"), [f], log=lambda m: None, workers=1)
        Image.open(os.path.join(spec.work, "frames", f"f{f:04d}.jpg")).convert("RGB").save(out, quality=92)
        return out
    if (st.get("world") or {}).get("look3d") and eng in (None, "three") and not os.environ.get("STUDIO_NO_BROWSER"):
        return style_frame_3d(style, out)
    im = Image.new("RGB", (1080, 1920), (0, 0, 0))
    try:  # style Flow/board/three: mẫu chữ thật của style (textstyle) trên nền đen
        art = textstyle.render("STEEL vs ICE", st, scale=1.0) if hasattr(textstyle, "render") else None
    except Exception:  # noqa: BLE001
        art = None
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", st["font"]), 120)
    if art is not None and hasattr(art, "image"):
        im.paste(art.image, ((1080 - art.image.width) // 2, 800), art.image)
    else:
        for i, ln in enumerate(("STEEL", "vs ICE") if st.get("uppercase", True) else ("Steel", "vs ice")):
            d.text(
                (540, 820 + i * 150),
                ln,
                font=f,
                fill=st.get("fill", "#FFFFFF"),
                anchor="mm",
                stroke_width=int(st.get("stroke") or 0) // 2,
                stroke_fill=st.get("stroke_color", "#000000"),
            )
    d.text((540, 1180), "1,000°C", font=f, fill=st.get("number_fill") or st.get("fill", "#FFFFFF"), anchor="mm")
    im.save(out, quality=92)
    return out


def style_frame_3d(style, out, props=None):
    """Style frame 9:16 thật của engine three.js: cảnh `stage` với đạo cụ kênh (mặc định bi thép nóng + đá + cốc thí
    nghiệm, `atlas.frame_props` của preset) theo look 3D + palette của style. Lỗi engine → thẻ chữ dự phòng."""
    from PIL import Image  # noqa: PLC0415

    from . import coderender  # noqa: PLC0415

    st = textstyle.load_style(style)
    types = props or (st.get("atlas") or {}).get("frame_props") or ["ball", "ice", "beaker"]
    if list(types) == ["ball", "ice", "beaker"]:   # bố cục chuẩn của kênh: bi thép nóng trên cốc nước đá, hơi bốc
        pr = [{"id": "beaker", "type": "beaker", "at": [0, 0, 0], "r": 0.2, "h": 0.42, "water": 0.72},
              {"id": "ball", "type": "ball", "at": [0, 0.66, 0], "r": 0.12, "hot": 0.9},
              {"id": "ice", "type": "ice", "at": [0.3, 0.04, 0.16]}]
        fx = [{"kind": "steam", "of": "beaker", "u": [0, 1], "r": 0.2}]
    else:
        n = len(types)
        pr = [{"id": f"p{i}", "type": t, "at": [(i - (n - 1) / 2) * 0.42, 0, 0], "scale": 1.3} for i, t in enumerate(types)]
        fx = []
    work = os.path.join(ROOT, "qa", "styles", "_work", style)
    spec = adapter.ShotSpec(sid="FRAME", engine="three", scene="stage",
                            params={"props": pr, "fx": fx, "frame": {"orbit": 6, "push": 0.06, "headroom": 0.16,
                                                                    "margin": 1.12}},
                            frames=24, fps=30, width=1080, height=1920, style=style, work=work)
    fdir = os.path.join(work, "frames")
    try:
        job = adapter.get("three").job(spec)
        coderender.render(job, fdir, frames=[16], workers=1, log=lambda *_: None)
        Image.open(os.path.join(fdir, "f0016.jpg")).convert("RGB").save(out, quality=92)
    except Exception:  # noqa: BLE001 — máy không có Edge/GPU: vẫn ra thẻ chữ
        os.environ["STUDIO_NO_BROWSER"] = "1"
        try:
            return style_frame(style, out)
        finally:
            os.environ.pop("STUDIO_NO_BROWSER", None)
    return out


def contact_sheet(names, out, cols=7, label=None):
    """Ghép style frame của `names` thành một ảnh (nhãn: id + engine + dòng phụ `label(name)`)."""
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    from . import styles  # noqa: PLC0415

    cw, ch, lab = 270, 480, 86
    rows = -(-len(names) // cols)
    sheet = Image.new("RGB", (cols * cw, rows * (ch + lab)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    f1 = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "RobotoMono-Variable.ttf"), 15)
    f2 = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "RobotoMono-Variable.ttf"), 13)
    for i, name in enumerate(names):
        p = os.path.join(ROOT, "qa", "styles", f"{name}.jpg")
        if not os.path.exists(p):
            style_frame(name, p)
        x, y = (i % cols) * cw, (i // cols) * (ch + lab)
        sheet.paste(Image.open(p).convert("RGB").resize((cw, ch)), (x, y))
        inf = styles.info(name)
        d.text((x + 8, y + ch + 8), name[:30], font=f1, fill=(236, 236, 236))
        d.text((x + 8, y + ch + 32), f"engine: {inf['engine']}", font=f2, fill=(150, 150, 150))
        d.text((x + 8, y + ch + 52), (label(name) if label else inf["source"] or "tool")[:34], font=f2, fill=(150, 150, 150))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    return out


def styles_gallery(cols=7):
    """qa/styles-gallery.png — mỗi style một style frame 9:16 nền đen + tên + engine + nguồn."""
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    from . import styles  # noqa: PLC0415

    names = styles.available()
    cw, ch, lab = 270, 480, 86
    rows = -(-len(names) // cols)
    sheet = Image.new("RGB", (cols * cw, rows * (ch + lab)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    f1 = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "RobotoMono-Variable.ttf"), 17)
    f2 = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "RobotoMono-Variable.ttf"), 13)
    for i, name in enumerate(names):
        p = style_frame(name, os.path.join(ROOT, "qa", "styles", f"{name}.jpg"))
        x, y = (i % cols) * cw, (i // cols) * (ch + lab)
        sheet.paste(Image.open(p).convert("RGB").resize((cw, ch)), (x, y))
        inf = styles.info(name)
        d.text((x + 8, y + ch + 8), name, font=f1, fill=(236, 236, 236))
        d.text((x + 8, y + ch + 34), f"engine: {inf['engine']}", font=f2, fill=(150, 150, 150))
        d.text((x + 8, y + ch + 54), f"nguồn: {inf['source'] or 'tool (vòng 1–6)'}"[:34], font=f2, fill=(150, 150, 150))
    out = os.path.join(ROOT, "qa", "styles-gallery.png")
    sheet.save(out)
    return out
