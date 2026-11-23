"""Tiện ích quanh engine code-shot: character test sheet, benchmark tốc độ render hai engine (docs/PERF.md)."""
import datetime
import json
import os
import platform
import shutil
import subprocess

from . import codeshot, coderender
from .common import ROOT

TEST = os.path.join(ROOT, "projects", "_engine_test")


def charsheet(style="forward"):
    """Render character test sheet của nhà khoa học (mọi biểu cảm + dáng tay) → docs/charsheet_<style>.jpg."""
    sid = f"CHARSHEET_{style.upper().replace('-', '_')}"
    job = codeshot.job_for(TEST, {}, {"id": sid, "code": {"scene": "charsheet", "params": {}}}, 2, style)
    coderender.render(job, codeshot.frames_dir(TEST, sid), [0], workers=1, log=lambda m: None)
    out = os.path.join(ROOT, "docs", f"charsheet_{style}.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copy(os.path.join(codeshot.frames_dir(TEST, sid), "f0000.jpg"), out)
    return out


def _cpu():
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                           capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or platform.processor()
    except Exception:  # noqa: BLE001
        return platform.processor()


def perf(frames=48, scene="scale", style="forward"):
    """Đo s/frame theo số worker (GPU) + một mốc CPU swiftshader. Ghi docs/PERF.md, trả về đường dẫn."""
    cores = os.cpu_count() or 2
    sid = "PERF"
    job = codeshot.job_for(TEST, {}, {"id": sid, "code": {"scene": scene, "params": {}}}, frames, style)
    rows = []
    for gpu, ws, n in [("auto", 1, frames), ("auto", 2, frames), ("auto", 4, frames), ("auto", 8, frames),
                       ("high", 1, frames), ("high", 2, frames), ("high", 8, frames),
                       ("off", 1, 6), ("off", 8, 16)]:
        out = os.path.join(codeshot.code_dir(TEST, sid), f"bench_{gpu}_{ws}")
        shutil.rmtree(out, ignore_errors=True)
        st = coderender.render(job, out, list(range(n)), workers=ws, gpu=gpu, log=lambda m: None)
        rows.append({"gpu": gpu, "workers": ws, "frames": n, **st})
        shutil.rmtree(out, ignore_errors=True)
    meta = {"date": f"{datetime.date.today():%d/%m/%Y}", "frames": frames, "scene": scene, "style": style,
            "cpu": _cpu(), "cores": cores, "platform": platform.platform()}
    with open(os.path.join(ROOT, "docs", "perf.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"meta": meta, "rows": rows}, f, ensure_ascii=False, indent=2)
    return write_perf_md()


def perf_board(board_path=None, workers=(1, 4, 8, 12), frames=None):
    """Benchmark engine board (Python/OpenCV, CPU): render chia đoạn theo số tiến trình → docs/perf_board.json + PERF.md.
    board_path mặc định: board.json mới nhất trong projects/*/work/board/."""
    import glob  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    from engines.board import render as brender  # noqa: PLC0415
    if not board_path:
        cands = glob.glob(os.path.join(ROOT, "projects", "*", "work", "board", "board.json"))
        if not cands:
            raise FileNotFoundError("Chưa có board.json nào — chạy một video style board-* tới stage text trước.")
        board_path = max(cands, key=os.path.getmtime)
    with open(board_path, encoding="utf-8") as f:
        b = json.load(f)
    if frames:
        b["frames"] = min(int(frames), int(b["frames"]))
    rows = []
    with tempfile.TemporaryDirectory() as d:
        bp = os.path.join(d, "board.json")
        with open(bp, "w", encoding="utf-8") as f:
            json.dump(b, f)
        for ws in workers:
            rows.append(brender.render_full(bp, os.path.join(d, f"bench_{ws}.mp4"), workers=ws, crf=17))
    meta = {"date": f"{datetime.date.today():%d/%m/%Y}",
            "board": os.path.relpath(os.path.abspath(board_path), ROOT).replace(os.sep, "/"),
            "frames": int(b["frames"]), "size": f"{b['width']}×{b['height']}", "style": b.get("style"),
            "items": len(b["items"]), "marks": len(b["marks"]), "inserts": len(b.get("inserts") or []),
            "cpu": _cpu(), "cores": os.cpu_count() or 2, "platform": platform.platform()}
    with open(os.path.join(ROOT, "docs", "perf_board.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"meta": meta, "rows": rows}, f, ensure_ascii=False, indent=2)
    return write_perf_md()


def _load(name):
    p = os.path.join(ROOT, "docs", name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, list):  # perf.json cũ (vòng 5) chỉ có danh sách dòng
        d = {"meta": {"date": "14/11/2026", "frames": 150, "scene": "scale", "style": "forward", "cpu": _cpu(),
                      "cores": os.cpu_count() or 2, "platform": platform.platform()}, "rows": d}
    return d


def write_perf_md():
    """docs/PERF.md = engine three.js (perf.json) + engine board (perf_board.json), cạnh nhau để so."""
    L = ["# PERF — tốc độ render các engine của `mode: code`", ""]
    t3, bd = _load("perf.json"), _load("perf_board.json")
    best3 = bestb = None
    if t3:
        m, rows = t3["meta"], t3["rows"]
        best3 = min((r for r in rows if r["gpu"] != "off"), key=lambda r: r["sec_per_frame"])
        sw = [r for r in rows if r["gpu"] == "off"]
        L += ["## 1. Engine three.js toon (engines/three/, Edge headless + WebGL)", "",
              f"Đo ngày {m['date']} bằng `python studio.py perf {m['frames']}` · cảnh `{m['scene']}` · "
              f"style `{m['style']}` · "
              "1080×1920 · JPEG q0.95.", "",
              f"- Máy: {m['cpu']} · {m['cores']} luồng CPU · {m['platform']}",
              f"- WebGL GPU: {best3['gl']}", f"- WebGL CPU (swiftshader): {sw[0]['gl'] if sw else '—'}", "",
              "| Chế độ | Worker | Frame | Tổng (s) | s/frame (wall) | s/frame/worker |", "|---|---|---|---|---|---|"]
        for r in rows:
            mode = {"auto": "GPU mặc định", "high": "GPU ép card rời", "off": "CPU swiftshader"}[r["gpu"]]
            L.append(f"| {mode} · {r['gl'][:38]} | {r['workers']} | {r['frames']} | {r['sec']} | "
                     f"{r['sec_per_frame']} | {r['sec_per_frame_per_worker']} |")
        L += ["", f"- Nhanh nhất: GPU, {best3['workers']} worker → **{best3['sec_per_frame']} s/frame** (wall). "
              "Nhiều worker hơn chỉ tranh GPU. Mặc định `code_render`: `gpu = high`, `workers = 0` (= 2), `resume = true`.",
              "- Kit gốc (một tiến trình, swiftshader): 3–10 s/frame."
              + (f" Swiftshader trên máy này: {sw[0]['sec_per_frame']} s/frame." if sw else ""), ""]
    if bd:
        m, rows = bd["meta"], bd["rows"]
        bestb = min(rows, key=lambda r: r["sec_per_frame"])
        one = next((r for r in rows if r["workers"] == 1), None)
        L += ["## 2. Engine board (engines/board/, Python + OpenCV, CPU)", "",
              f"Đo ngày {m['date']} bằng `python studio.py perf board` · `{m['board']}` (style `{m['style']}`, "
              f"{m['frames']} frame {m['size']}, {m['items']} thẻ, {m['marks']} dấu/nhãn, {m['inserts']} đoạn phim câm, "
              "có cả clip Flow toàn màn hình) · x264 CRF 17 · chia đoạn theo tiến trình rồi nối `concat -c copy`.", "",
              f"- Máy: {m['cpu']} · {m['cores']} luồng CPU", "",
              "| Tiến trình | Frame | Tổng (s) | s/frame (wall) | s/frame/tiến trình |", "|---|---|---|---|---|"]
        for r in rows:
            L.append(f"| {r['workers']} | {r['frames']} | {r['sec']} | {r['sec_per_frame']} | "
                     f"{r['sec_per_frame_per_worker']} |")
        L += ["", f"- Nhanh nhất: {bestb['workers']} tiến trình → **{bestb['sec_per_frame']} s/frame** (wall) → video 40 s "
              f"(1.200 frame) ≈ **{1200 * bestb['sec_per_frame'] / 60:.1f} phút**."
              + (f" Một tiến trình: {one['sec_per_frame']} s/frame (plugin gốc ghi 0.15–0.3 s/frame ở 1920×1080)."
                 if one else ""),
              "- Mặc định (`config/channel.json → board`): `workers = 0` (= số luồng − 2, tối đa 12), "
              "mỗi tiến trình 1 luồng "
              "OpenCV (tránh tranh CPU), `crf = 17`.", ""]
    if best3 and bestb:
        L += ["## So sánh", "",
              f"- three.js (GPU): {best3['sec_per_frame']} s/frame — chỉ render shot có `code.scene`.",
              f"- board (CPU): {bestb['sec_per_frame']} s/frame — CẢ video board_spine (bảng, clip Flow, dấu đỏ, phim câm, "
              "grain), không cần GPU hay trình duyệt.",
              "- Video board_spine có cảnh three.js (thẻ 'màn hình nhỏ') thì cảnh đó render bằng three.js trước, "
              "engine board "
              "dùng frame của nó làm texture.", ""]
    from . import enginebench  # noqa: PLC0415 — mục 3–4: engine html/manim + quyết định HyperFrames (vòng 7)
    L += enginebench.perf_section()
    p = os.path.join(ROOT, "docs", "PERF.md")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    return p
