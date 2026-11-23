"""`python studio.py clean <slug> [--yes]` — dọn file trung gian SINH LẠI ĐƯỢC của một dự án (AUD-807/1104).

Xoá: work/video.mp4 (bản trùng của out/final.mp4 trước khi trộn tiếng), work/board/ (frame/đoạn engine board),
work/code/*/frames (frame shot code — RESUME sẽ dựng lại khi cần), work/ingest/*.mp4 (dựng lại từ clips/),
*.part.mp4 / *.tmp sót lại, qa/look/_work. Giữ nguyên: storyboard, clips/, audio/, out/ (+ versions/), thumbnails/,
qa/report.*, work/*.json. Mặc định chỉ liệt kê; --yes mới xoá.
"""
import glob
import os
import shutil


def targets(proj):
    w = os.path.join(proj, "work")
    pats = [os.path.join(w, "video.mp4"), os.path.join(w, "board"), os.path.join(w, "code", "*", "frames"),
            os.path.join(w, "ingest", "*.mp4"), os.path.join(proj, "**", "*.part.mp4"), os.path.join(proj, "**", "*.tmp"),
            os.path.join(proj, "qa", "look", "_work")]
    out = []
    for p in pats:
        out += glob.glob(p, recursive=True)
    return sorted(set(out))


def size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)


def run(proj, apply=False, log=print):
    ts = targets(proj)
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
