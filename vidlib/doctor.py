"""`python studio.py doctor` — kiểm môi trường + cấu hình trong một lệnh (AUD-1302).

Mỗi dòng: OK / WARN / FAIL. FAIL → exit 1 (pipeline sẽ hỏng). WARN → chạy được nhưng thiếu một phần (vd không có
Tesseract → mất kiểm OCR; không có Manim → bỏ style physics-diagram). Không bao giờ in giá trị API key.
"""
import glob
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys

from .common import CONFIG_DIR, PROJECTS, ROOT, env, ffbin

REQ = [("pillow", "Pillow", True), ("numpy", "numpy", True), ("opencv-python", "OpenCV", True),
       ("playwright", "Playwright (engine three/html)", True), ("manim", "Manim CE (engine manim)", False)]


def _row(level, what, detail=""):
    return {"level": level, "what": what, "detail": detail}


def _ver(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).splitlines()[0] if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def checks(browser=True):
    out = []
    py = sys.version_info
    out.append(_row("OK" if py >= (3, 10) else "FAIL", "Python ≥ 3.10", platform.python_version()))
    for pkg, name, need in REQ:
        try:
            out.append(_row("OK", name, importlib.metadata.version(pkg)))
        except importlib.metadata.PackageNotFoundError:
            out.append(_row("FAIL" if need else "WARN", name, "chưa cài — pip install -r requirements.txt"))
    for tool in ("ffmpeg", "ffprobe"):
        v = _ver([ffbin(tool), "-version"])
        out.append(_row("OK" if v else "FAIL", tool, (v or "không chạy được — winget install Gyan.FFmpeg")[:90]))
    enc = _ver([ffbin("ffmpeg"), "-hide_banner", "-h", "encoder=libx264"])
    out.append(_row("OK" if enc else "FAIL", "ffmpeg có libx264", "có" if enc else "thiếu libx264"))
    if browser:
        out.append(_browser())
    from . import ocr  # noqa: PLC0415
    out.append(_row("OK" if ocr.available() else "WARN", "Tesseract + tessdata (OCR trong QA)",
                    ocr.tesseract() or "không có → QA bỏ kiểm OCR (cài Tesseract-OCR)"))
    for key in ("ELEVENLABS_API_KEY",):
        out.append(_row("OK" if env(key) else "WARN", f"{key} (.env)", "có" if env(key) else
                        "chưa có → chỉ chạy được --dry-run cho giọng"))
    for key in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        out.append(_row("OK" if (os.environ.get(key) or env(key)) else "WARN", f"{key} (tuỳ chọn, --ai)",
                        "có" if (os.environ.get(key) or env(key)) else "không có (dùng /video trong Claude Code)"))
    bad = []
    for p in glob.glob(os.path.join(CONFIG_DIR, "*.json")) + glob.glob(os.path.join(ROOT, "styles", "*.json")) + \
            [os.path.join(ROOT, "rights", "ledger.json")]:
        try:
            with open(p, encoding="utf-8") as fh:
                json.load(fh)
        except (OSError, ValueError) as e:
            bad.append(f"{os.path.relpath(p, ROOT)}: {e}")
    out.append(_row("FAIL" if bad else "OK", "JSON cấu hình + style đọc được", "; ".join(bad)[:200] or "tất cả"))
    out.append(_fonts())
    out.append(_atlas())
    free = shutil.disk_usage(ROOT).free / 1e9
    out.append(_row("OK" if free > 10 else "WARN" if free > 3 else "FAIL", "Dung lượng trống", f"{free:.1f} GB"))
    try:
        os.makedirs(PROJECTS, exist_ok=True)
        t = os.path.join(PROJECTS, ".doctor-write-test")
        with open(t, "w") as fh:
            fh.write("x")
        os.remove(t)
        out.append(_row("OK", "Ghi được projects/", PROJECTS))
    except OSError as e:
        out.append(_row("FAIL", "Ghi được projects/", str(e)))
    from . import rights  # noqa: PLC0415
    dec = {k: v for k, v in rights.ledger().get("decisions", {}).items() if not k.startswith("_")}
    pend = [k for k, v in dec.items() if str(v).lower() in ("unknown", "pending", "?")]
    out.append(_row("WARN" if pend else "OK", "Quyết định bản quyền (rights/ledger.json)",
                    ("chờ chủ kênh: " + ", ".join(pend)) if pend else "đã chốt"))
    return out


def _browser():
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        from .coderender import cfg  # noqa: PLC0415
        ch = cfg().get("channel") or "msedge"
        with sync_playwright() as p:
            b = p.chromium.launch(channel=ch or None, headless=True)
            v = b.version
            b.close()
        return _row("OK", f"Trình duyệt headless ({ch})", v)
    except Exception as e:  # noqa: BLE001
        return _row("FAIL", "Trình duyệt headless (Edge/Chromium cho engine three/html)",
                    str(e).splitlines()[0][:120] + " — cài Microsoft Edge hoặc: python -m playwright install chromium")


def _fonts():
    from . import textstyle  # noqa: PLC0415
    miss = set()
    for sid in textstyle.list_styles():
        try:
            st = textstyle.load_style(sid)
        except Exception:  # noqa: BLE001
            continue
        for f in {st.get("font"), (st.get("html") or {}).get("font")} - {None}:
            if not os.path.exists(os.path.join(ROOT, "assets", "fonts", f)):
                miss.add(f)
    return _row("FAIL" if miss else "OK", "Font mọi style có trong assets/fonts/", ", ".join(sorted(miss)) or "đủ")


def _atlas():
    from . import atlas  # noqa: PLC0415
    errs = [f"{atlas.style_id(e)}: {'; '.join(x)}" for e in atlas.entries() if (x := atlas.check(e))]
    return _row("FAIL" if errs else "OK", "Preset 3D Style Atlas hợp lệ (không chép nguyên văn, đủ trường)",
                "; ".join(errs)[:200] or f"{len(atlas.entries())} preset")


def run(browser=True, log=print):
    rows = checks(browser)
    w = max(len(r["what"]) for r in rows)
    for r in rows:
        log(f"  {r['level']:<4}  {r['what']:<{w}}  {r['detail']}")
    n_fail = sum(r["level"] == "FAIL" for r in rows)
    n_warn = sum(r["level"] == "WARN" for r in rows)
    log(f"  → {len(rows)} mục · {n_fail} FAIL · {n_warn} WARN")
    return 1 if n_fail else 0
