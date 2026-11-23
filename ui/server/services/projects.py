"""Đọc trạng thái dự án (projects/<slug>/) cho UI — chỉ đọc file pipeline đã ghi, không chạy stage nào."""
import os
import re

from vidlib import pipeline, textstyle
from vidlib.common import FPS, PROJECTS, load_json

SLUG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,95}$")   # `_*` = dự án thử (ẩn mặc định, vẫn mở được)
OUTPUTS = [  # (khoá, đường dẫn tương đối, nhãn tiếng Việt)
    ("final", "out/final.mp4", "Video Shorts 9:16"),
    ("endscreen", "out/endscreen_16x9.mp4", "End screen 16:9"),
    ("captions", "out/captions.srt", "Phụ đề .srt"),
    ("publish", "publish.md", "Tiêu đề / mô tả / hashtag"),
    ("report", "qa/report.html", "Báo cáo QA"),
    ("look", "qa/look/sheet.jpg", "Contact sheet look-check"),
    ("contact", "thumbnails/contact-sheet.png", "Thumbnail (tất cả)"),
    ("scripts", "scripts.html", "Trang prompt Flow"),
    ("brief", "brief.md", "Brief cho LLM"),
    ("storyboard", "storyboard.json", "storyboard.json"),
]
STATUS_LABEL = {
    "done": "Hoàn tất", "waiting_clips": "Chờ clip Flow", "look_check": "Chờ duyệt look",
    "need_storyboard": "Cần storyboard", "storyboard_invalid": "Storyboard lỗi", "lint_failed": "Lint lỗi",
    "confirm_map": "Chờ xác nhận map clip",
    "running": "Đang chạy", "failed": "Lỗi", "new": "Mới", "draft": "Bản nháp",
}


class NotFound(Exception):
    pass


def proj_dir(slug):
    if not SLUG_RE.match(slug or ""):
        raise NotFound(slug)
    p = os.path.join(PROJECTS, slug)
    if not os.path.isdir(p):
        raise NotFound(slug)
    return p


def _read(p, default=""):
    try:
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return default


def _mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0


def _shot_engine(shot, style):
    from vidlib import codeshot  # noqa: PLC0415
    mode = shot.get("mode_resolved") or shot.get("mode")
    c = shot.get("code") or {}
    if c.get("engine") == "board" or (mode == "code" and not c.get("scene") and shot.get("beat_recipe")):
        return "board"
    if mode == "code" and c.get("scene"):
        try:
            return codeshot.engine_of(shot, style) or "three"
        except Exception:  # noqa: BLE001
            return "three"
    return "flow"


def _uses_flow(style):
    from vidlib import styles  # noqa: PLC0415
    try:
        return styles.uses_flow(style)
    except Exception:  # noqa: BLE001 — style đã xoá/đổi tên
        return None


def _qa(p):
    qj = os.path.join(p, "work", "qa.json")
    if os.path.exists(qj):                           # vòng 9: cổng QA đỏ/vàng/xanh
        q = load_json(qj, {}) or {}
        if q.get("verdict"):
            rows = [{"name": r["label"], "value": r["value"], "ok": r["ok"], "level": r["level"]}
                    for r in q.get("rows") or []]
            return {"verdict": q["verdict"], "checks": rows}
    md = _read(os.path.join(p, "qa", "report.md"))
    if not md:
        return None
    m = re.search(r"Kết quả:\s*\*\*([^*]+)\*\*", md)
    checks = []
    for row in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(✓|✗|✖|⚠|—)\s*\|\s*$", md, re.M):
        if row[0] not in ("Kiểm tra",):
            checks.append({"name": row[0], "value": row[1], "ok": row[2] == "✓"})
    return {"verdict": (m.group(1).strip() if m else None), "checks": checks}


def _status(p, sb, last_job):
    if last_job and last_job.get("status") in ("running", "queued"):
        return "running"
    if last_job and last_job.get("stage"):
        if last_job["stage"] == "done" and os.path.exists(os.path.join(p, "out", "final.mp4")):
            return "done"
        if last_job["stage"] != "done":
            return last_job["stage"] if last_job["stage"] in STATUS_LABEL else "failed"
    if os.path.exists(os.path.join(p, "out", "final.mp4")):
        return "done"
    if not sb:
        return "need_storyboard" if os.path.exists(os.path.join(p, "brief.md")) else "new"
    return "draft"


def _stage_progress(p, sb, status):
    """Stage đã qua (suy từ file đầu ra) — đủ cho thanh tiến trình, không thay thế state.json của pipeline."""
    have = {
        "idea": os.path.exists(os.path.join(p, "idea.txt")),
        "script": bool(sb),
        "storyboard": bool(sb),
        "prompts": os.path.exists(os.path.join(p, "prompts.txt")),
        "page": os.path.exists(os.path.join(p, "scripts.html")),
        "voice": any(os.path.exists(os.path.join(p, "audio", f)) for f in ("vo.mp3", "vo.wav")),
        "assemble": os.path.exists(os.path.join(p, "work", "timeline.json")),
        "audio": os.path.exists(os.path.join(p, "work", "mix.wav")),
        "look": os.path.exists(os.path.join(p, "qa", "look", "sheet.jpg")),
        "render": os.path.exists(os.path.join(p, "out", "final.mp4")),
        "thumbnails": os.path.exists(os.path.join(p, "thumbnails", "contact-sheet.png")),
        "publish": os.path.exists(os.path.join(p, "publish.md")),
        "qa": os.path.exists(os.path.join(p, "qa", "report.html")),
    }
    stages = pipeline.STAGES
    done = set()
    last = -1
    for i, s in enumerate(stages):
        if have.get(s):
            last = i
    for i, s in enumerate(stages):
        if i <= last:
            done.add(s)
    blocked = {"waiting_clips": "clips", "look_check": "look", "need_storyboard": "storyboard",
               "storyboard_invalid": "storyboard", "lint_failed": "storyboard", "confirm_map": "ingest"}.get(status)
    return [{"id": s, "state": ("blocked" if s == blocked else "done" if s in done and s != blocked else "todo")}
            for s in stages]


def _thumb(p):
    for rel in ("thumbnails/T1_9x16.png", "thumbnails/T1_youtube.png", "qa/look/sheet.jpg"):
        if os.path.exists(os.path.join(p, rel)):
            return rel
    return None


def summary(slug, last_job=None):
    p = proj_dir(slug)
    sb = load_json(os.path.join(p, "storyboard.json"), {}) if os.path.exists(os.path.join(p, "storyboard.json")) else {}
    plan = load_json(os.path.join(p, "plan.json"), {}) if os.path.exists(os.path.join(p, "plan.json")) else {}
    tl = load_json(os.path.join(p, "work", "timeline.json"), {}) if os.path.exists(
        os.path.join(p, "work", "timeline.json")) else {}
    style = sb.get("style_resolved") or (sb.get("style") if sb.get("style") != "auto" else None) or plan.get("style")
    voice = plan.get("voice") or sb.get("voice_resolved") or sb.get("voice") or {}
    status = _status(p, sb, last_job)
    shots = sb.get("shots") or []
    mix = {}
    for s in shots:
        e = _shot_engine(s, style)
        mix[e] = mix.get(e, 0) + 1
    qa = _qa(p)
    files = [os.path.join(p, f) for f in ("storyboard.json", "out/final.mp4", "idea.txt", "plan.json", "work/state.json")]
    return {
        "slug": slug, "idea": _read(os.path.join(p, "idea.txt")).strip(), "title": sb.get("title") or "",
        "style": style, "style_name": textstyle.load_style(style).get("name", style) if style else None,
        "voice": voice.get("name") if isinstance(voice, dict) else voice,
        "narrative": sb.get("narrative_resolved") or plan.get("narrative"),
        "uses_flow": plan.get("uses_flow") if plan.get("uses_flow") is not None else (
            _uses_flow(style) if style else None), "shots": len(shots), "mix": mix,
        "duration": tl.get("duration"), "status": status, "status_label": STATUS_LABEL.get(status, status),
        "qa": qa["verdict"] if qa else None, "thumb": _thumb(p),
        "has_final": os.path.exists(os.path.join(p, "out", "final.mp4")),
        "updated": max(_mtime(f) for f in files), "demo": slug.startswith(("_", "cmp-")),
        "dry_run": os.path.exists(os.path.join(p, "work", "DRYRUN")),
        "cost": (load_json(os.path.join(p, "work", "cost.json"), {}) or {}).get("summary")
        if os.path.exists(os.path.join(p, "work", "cost.json")) else None,
        "version": (load_json(os.path.join(p, "out", "manifest.json"), {}) or {}).get("version")
        if os.path.exists(os.path.join(p, "out", "manifest.json")) else None,
    }


def list_all(last_jobs):
    if not os.path.isdir(PROJECTS):
        return []
    out = []
    for slug in os.listdir(PROJECTS):
        if not os.path.isdir(os.path.join(PROJECTS, slug)) or not SLUG_RE.match(slug):
            continue
        try:
            out.append(summary(slug, last_jobs.get(slug)))
        except Exception as e:  # noqa: BLE001 — một dự án hỏng không làm sập danh sách
            out.append({"slug": slug, "status": "failed", "status_label": f"Không đọc được: {e}", "updated": 0,
                        "mix": {}, "shots": 0})
    return sorted(out, key=lambda x: -(x.get("updated") or 0))


def detail(slug, last_job=None):
    p = proj_dir(slug)
    s = summary(slug, last_job)
    sb = load_json(os.path.join(p, "storyboard.json"), {}) if os.path.exists(os.path.join(p, "storyboard.json")) else {}
    tl = load_json(os.path.join(p, "work", "timeline.json"), {}) if os.path.exists(
        os.path.join(p, "work", "timeline.json")) else {}
    prompts = load_json(os.path.join(p, "work", "prompts.json"), {}) if os.path.exists(
        os.path.join(p, "work", "prompts.json")) else {}
    segs = {x["sid"]: x for x in tl.get("segments", [])}
    clips = {}
    cdir = os.path.join(p, "clips")
    if os.path.isdir(cdir):
        from vidlib import ingest  # noqa: PLC0415
        for f in os.listdir(cdir):
            sid = ingest.shot_id_from_name(f)
            if sid:
                clips[sid] = f
    shots = []
    for sh in sb.get("shots") or []:
        eng = _shot_engine(sh, s["style"])
        seg = segs.get(sh["id"]) or {}
        c = sh.get("code") or {}
        pr = prompts.get(sh["id"]) or {}
        frames_dir = os.path.join(p, "work", "code", sh["id"], "frames")
        still = None
        if os.path.isdir(frames_dir):
            fs = sorted(f for f in os.listdir(frames_dir) if f.endswith(".jpg"))
            if fs:
                still = f"work/code/{sh['id']}/frames/{fs[len(fs) // 2]}"
        shots.append({
            "id": sh["id"], "beat": sh.get("beat"), "mode": sh.get("mode_resolved") or sh.get("mode"), "engine": eng,
            "scene": c.get("scene") or sh.get("beat_recipe"), "vo": sh.get("vo", ""),
            "start": round(seg["start_f"] / FPS, 2) if seg else None, "dur": seg.get("dur") or (
                round(seg["n"] / FPS, 2) if seg else sh.get("target_sec")),
            "needs_clip": eng == "flow", "clip": clips.get(sh["id"]), "still": still,
            "prompts": {k: v for k, v in pr.items() if isinstance(v, str) and k != "mode"},
        })
    outputs = [{"key": k, "path": rel, "label": lab, "size": os.path.getsize(os.path.join(p, rel))}
               for k, rel, lab in OUTPUTS if os.path.exists(os.path.join(p, rel))]
    thumbs = sorted(f for f in os.listdir(os.path.join(p, "thumbnails")) if f.endswith(".png") and f.startswith("T")) \
        if os.path.isdir(os.path.join(p, "thumbnails")) else []
    s.update({
        "stages": _stage_progress(p, sb, s["status"]), "shots_detail": shots, "outputs": outputs,
        "thumbnails": [f"thumbnails/{t}" for t in thumbs], "qa_detail": _qa(p),
        "publish_md": _read(os.path.join(p, "publish.md")), "topic": sb.get("topic"), "hook": sb.get("hook"),
        "truth": sb.get("truth"), "total": tl.get("duration"),
        "style_bible": _read(os.path.join(p, "prompts.txt"))[:6000],
    })
    return s
