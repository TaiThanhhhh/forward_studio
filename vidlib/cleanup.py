"""`python studio.py clean <slug|--all> [--yes]` — dọn file trung gian SINH LẠI ĐƯỢC + version cũ (AUD-807/1104/Vòng 16).

Xoá: work/video.mp4, work/board/, work/code/*/frames, work/ingest/*.mp4, *.part.mp4 / *.tmp, qa/look/_work,
các bản out/versions/vNNN cũ (chỉ giữ bản mới nhất), thư mục rỗng clips/frames/refs, và scripts.html/prompts.txt thừa
khi dự án 100% code. Giữ nguyên: storyboard, audio/, out/final.mp4, out/deliver/, bản version mới nhất, publish.md,
qa/report.*. Mặc định chỉ liệt kê; --yes mới xoá.
"""
import glob
import os
import shutil

from .common import PROJECTS, load_json


def _is_code_only(proj):
    sb = load_json(os.path.join(proj, "storyboard.json"), {})
    shots = sb.get("shots") or []
    return bool(shots) and all(s.get("mode_resolved", s.get("mode")) == "code" for s in shots)


def targets(proj, keep_versions=1):
    w = os.path.join(proj, "work")
    pats = [os.path.join(w, "video.mp4"), os.path.join(w, "board"), os.path.join(w, "code", "*", "frames"),
            os.path.join(w, "ingest", "*.mp4"), os.path.join(proj, "**", "*.part.mp4"), os.path.join(proj, "**", "*.tmp"),
            os.path.join(proj, "qa", "look", "_work")]
    out = []
    for p in pats:
        out += glob.glob(p, recursive=True)
    vs = sorted(glob.glob(os.path.join(proj, "out", "versions", "v[0-9][0-9][0-9]")))
    if keep_versions is not None and len(vs) > keep_versions:
        out += vs[:-keep_versions] if keep_versions > 0 else vs
    for empty_dir in ("clips", "frames", "refs"):
        dp = os.path.join(proj, empty_dir)
        if os.path.isdir(dp) and not os.listdir(dp):
            out.append(dp)
    if _is_code_only(proj):
        for rel in ("scripts.html", "prompts.txt"):
            fp = os.path.join(proj, rel)
            if os.path.isfile(fp):
                out.append(fp)
    return sorted(set(out))


def size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)


def run(proj, apply=False, log=print, keep_versions=1):
    ts = targets(proj, keep_versions=keep_versions)
    total = 0
    for p in ts:
        n = size(p)
        total += n
        log(f"  {'xoá' if apply else 'sẽ xoá'}  {n / 1e6:8.1f} MB  {os.path.relpath(p, proj)}")
        if apply:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                os.remove(p)
    log(f"  → {total / 1e6:.1f} MB" + ("" if apply else " (chạy lại với --yes để xoá thật)"))
    return 0


def run_all(apply=False, log=print, keep_versions=1):
    if not os.path.isdir(PROJECTS):
        return 0
    for slug in sorted(os.listdir(PROJECTS)):
        d = os.path.join(PROJECTS, slug)
        if not os.path.isdir(d) or slug.startswith("."):
            continue
        ts = targets(d, keep_versions=keep_versions)
        if not ts:
            continue
        log(f"▶ {slug}")
        run(d, apply=apply, log=log, keep_versions=keep_versions)
    return 0
