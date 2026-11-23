"""API v2 cho UI công đoạn (Projects · Script · Board · Generate · Edit · Review · Deliver · Library).

Chỉ ĐỌC file pipeline đã ghi (+ một file riêng của UI: projects/<slug>/review/review.json cho comment/duyệt).
Mọi thay đổi tới video vẫn đi qua job `studio.py …` (services/jobs.py).
"""
import datetime
import glob
import json
import os
import re
import time
import uuid

from vidlib.common import CONFIG_DIR, PROJECTS, ROOT, load_json, save_json

from . import projects


def _j(p, default=None):
    return load_json(p, default) if os.path.exists(p) else default


def _rel(p, base):
    return os.path.relpath(p, base).replace("\\", "/")


def keyframe_order(shots):
    """Thứ tự tạo ảnh Flow theo cây keyframe: ảnh được dùng làm nguồn (seed_from) phải có trước. Trả về
    [{id, depends: [...], level}] — level 0 = tạo trước."""
    ids = [s["id"] for s in shots]
    dep = {}
    for s in shots:
        d = set()
        for k in ("start_frame", "end_frame"):
            src = (s.get(k) or {}).get("seed_from")
            if src and src in ids and src != s["id"]:
                d.add(src)
        if s.get("continues_from") in ids:
            d.add(s["continues_from"])
        dep[s["id"]] = sorted(d)
    level = {}

    def lv(i, seen=()):
        if i in level:
            return level[i]
        if i in seen:
            return 0
        level[i] = 1 + max((lv(x, (*seen, i)) for x in dep[i]), default=-1)
        return level[i]

    for i in ids:
        lv(i)
    return sorted(({"id": i, "depends": dep[i], "level": level[i]} for i in ids), key=lambda r: (r["level"], ids.index(r["id"])))


def vo_info(p):
    al = _j(os.path.join(p, "audio", "vo_alignment.json"), {}) or {}
    takes = []
    for f in sorted(glob.glob(os.path.join(p, "audio", "vo.*"))):
        b = os.path.basename(f)
        if b.endswith((".mp3", ".wav")):
            takes.append({"file": f"audio/{b}", "current": b in ("vo.mp3", "vo.wav"), "mtime": os.path.getmtime(f),
                          "size": os.path.getsize(f)})
    return {"takes": sorted(takes, key=lambda t: (not t["current"], -t["mtime"])), "words": al.get("words") or [],
            "voice": (al.get("voice") or {}).get("name"), "model": al.get("model_id"), "duration": al.get("duration"),
            "wps": al.get("words_per_sec")}


def versions(p):
    out = []
    for d in sorted(glob.glob(os.path.join(p, "out", "versions", "v[0-9][0-9][0-9]"))):
        m = _j(os.path.join(d, "manifest.json"), {}) or {}
        out.append({"id": os.path.basename(d), "file": _rel(os.path.join(d, "final.mp4"), p), "created": m.get("created"),
                    "verdict": (m.get("qa") or {}).get("verdict"), "commit": (m.get("git") or {}).get("commit"),
                    "style": m.get("style")})
    return out


def workspace(slug, last_job=None):
    from vidlib import sbedit  # noqa: PLC0415
    d = projects.detail(slug, last_job)
    p = projects.proj_dir(slug)
    sb_path = os.path.join(p, "storyboard.json")
    sb_raw = projects._read(sb_path)[:200000] if os.path.exists(sb_path) else ""
    sb = _j(sb_path, {}) or {}
    shots = sb.get("shots") or []
    by = {s["id"]: s for s in shots if isinstance(s, dict) and s.get("id")}
    previews = {
        os.path.splitext(os.path.basename(f))[0]: f"work/preview/{os.path.basename(f)}"
        for f in sorted(glob.glob(os.path.join(p, "work", "preview", "*.jpg")))
    }
    for s in d.get("shots_detail") or []:
        src = by.get(s["id"], {})
        s["frames"] = {k: (src.get(f"{k}_frame") or {}).get("file") for k in ("start", "end")
                       if (src.get(f"{k}_frame") or {}).get("file")
                       and os.path.exists(os.path.join(p, (src.get(f"{k}_frame") or {}).get("file")))}
        s["seed_from"] = {k: (src.get(f"{k}_frame") or {}).get("seed_from") for k in ("start", "end")}
        s["refs"] = src.get("refs") or []
        s["subject"] = src.get("subject", "")
        s["camera"] = src.get("camera", "")
        s["action"] = src.get("action")
        s["text_fx"] = src.get("text_fx") or []
        s["onscreen"] = src.get("onscreen")
        s["hold"] = bool(src.get("hold"))
        s["target_sec"] = src.get("target_sec")
        s["code"] = src.get("code") or {}
        s["override"] = src.get("override") or {}
        s["preview"] = previews.get(s["id"])
        s["preview_mtime"] = os.path.getmtime(os.path.join(p, previews[s["id"]])) if s["id"] in previews else 0
    qa = _j(os.path.join(p, "work", "qa.json"), {}) or {}
    sb_chk = None
    if os.path.exists(sb_path) and sb:
        try:
            sb_chk = sbedit.check(p, sb, sb_raw)
        except Exception as e:  # noqa: BLE001
            sb_chk = {"ok": False, "errors": [{"msg": str(e), "path": "", "line": None}], "warnings": [], "summary": {}}
    d.update({
        "workspace": 2,
        "keyframes": keyframe_order(shots),
        "ingredients": [{"id": i.get("id"), "desc": i.get("desc"), "prompt": i.get("image_prompt")} for i in sb.get("ingredients") or []],
        "timeline": _j(os.path.join(p, "work", "timeline.json"), {}) or {},
        "captions": _j(os.path.join(p, "work", "captions.json"), []) or [],
        "trims": _j(os.path.join(p, "work", "trim.json"), {}) or {},
        "stems": [f"work/stems/{os.path.basename(f)}" for f in sorted(glob.glob(os.path.join(p, "work", "stems", "*.wav")))],
        "vo": vo_info(p),
        "qa": {"verdict": qa.get("verdict"), "legacy_ok": qa.get("ok") if qa and not qa.get("verdict") else None,
               "rows": qa.get("rows") or [], "gate": qa.get("gate") or {}},
        "deliver": _j(os.path.join(p, "out", "deliver", "deliver.json"), {}) or {},
        "rights": _j(os.path.join(p, "out", "rights.json"), {}) or {},
        "manifest": _j(os.path.join(p, "out", "manifest.json"), {}) or {},
        "versions": versions(p),
        "cost": (_j(os.path.join(p, "work", "cost.json"), {}) or {}).get("summary") or {},
        "review": review_get(slug),
        "script_md": projects._read(os.path.join(p, "script.md"))[:20000],
        "brief_md": projects._read(os.path.join(p, "brief.md"))[:40000],
        "sb_raw": sb_raw,
        "sb_check": sb_chk,
        "sb_history": sbedit.history(p),
        "previews": previews,
        "plan": _j(os.path.join(p, "plan.json"), {}) or {},
        "seeds": _j(os.path.join(p, "work", "seeds.json"), {}) or {},
    })
    return d


# ------------------------------------------------------------------ review (file riêng của UI)
def _review_path(slug):
    return os.path.join(projects.proj_dir(slug), "review", "review.json")


def review_get(slug):
    return _j(_review_path(slug), {"status": "pending", "comments": [], "history": []}) or {}


STATUSES = ("pending", "approved", "changes")


def review_post(slug, body):
    """body: {op: add|resolve|delete|status|restore, …}. Trả về review mới."""
    r = review_get(slug)
    op = body.get("op")
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    if op == "add":
        text = str(body.get("text") or "").strip()[:2000]
        t = float(body.get("t") or 0)
        if not text or not (0 <= t < 3600):
            raise ValueError("Comment cần nội dung và timecode hợp lệ.")
        draw = body.get("drawing") or []
        draw = [[[round(float(x), 4), round(float(y), 4)] for x, y in stroke[:400]] for stroke in draw[:20]]
        c = {"id": uuid.uuid4().hex[:8], "t": round(t, 3), "frame": int(round(t * 30)), "text": text, "drawing": draw,
             "version": str(body.get("version") or "latest")[:16], "created": now, "resolved": False}
        r.setdefault("comments", []).append(c)
    elif op in ("resolve", "delete", "restore"):
        cid = str(body.get("id") or "")
        cs = r.get("comments") or []
        hit = next((c for c in cs if c["id"] == cid), None)
        if not hit and op != "restore":
            raise ValueError("Không có comment này.")
        if op == "resolve":
            hit["resolved"] = not hit.get("resolved")
        elif op == "delete":
            r["comments"] = [c for c in cs if c["id"] != cid]
            r.setdefault("trash", []).append(hit)
        else:
            tr = r.get("trash") or []
            back = next((c for c in tr if c["id"] == cid), None)
            if back:
                r["trash"] = [c for c in tr if c["id"] != cid]
                cs.append(back)
                r["comments"] = sorted(cs, key=lambda c: c["t"])
    elif op == "status":
        st = body.get("status")
        if st not in STATUSES:
            raise ValueError("Trạng thái không hợp lệ.")
        r["status"] = st
        r.setdefault("history", []).append({"status": st, "at": now, "version": str(body.get("version") or "latest")[:16]})
    else:
        raise ValueError("op không hợp lệ.")
    r["comments"] = sorted(r.get("comments") or [], key=lambda c: c["t"])
    r["updated"] = now
    save_json(_review_path(slug), r)
    return r


# ------------------------------------------------------------------ thư viện
def delivery():
    return _j(os.path.join(CONFIG_DIR, "delivery.json"), {}) or {}


def atlas_raw(n):
    """Bản gốc của style atlas số n (chỉ máy này — vendor/3d-style-atlas/raw/ gitignore)."""
    hits = glob.glob(os.path.join(ROOT, "vendor", "3d-style-atlas", "raw", f"{int(n):02d}-*.json"))
    if not hits:
        return None
    return _j(hits[0], None)


def assets():
    led = _j(os.path.join(ROOT, "rights", "ledger.json"), {}) or {}
    fonts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "assets", "fonts", "*"))):
        if f.lower().endswith((".ttf", ".otf")):
            from vidlib import rights  # noqa: PLC0415
            e = rights.font_entry(os.path.basename(f)) or {}
            fonts.append({"file": os.path.basename(f), "license": e.get("license"), "commercial": rights.commercial(e) if e else
                          "unknown", "size": os.path.getsize(f)})
    sfx = [{"name": os.path.splitext(os.path.basename(f))[0], "file": _rel(f, os.path.join(ROOT, "assets", "sfx")), "builtin": "_builtin" in f}
           for f in sorted(glob.glob(os.path.join(ROOT, "assets", "sfx", "**", "*.wav"), recursive=True))]
    return {"fonts": fonts, "sfx": sfx, "ledger": led}


def session_cost(hours=24):
    """Chi phí trong `hours` giờ gần nhất trên mọi dự án (thanh trạng thái)."""
    from vidlib import cost  # noqa: PLC0415
    cut = time.time() - hours * 3600
    ev = []
    for f in glob.glob(os.path.join(PROJECTS, "*", "work", "cost.json")):
        if os.path.getmtime(f) < cut:
            continue
        for e in (_j(f, {}) or {}).get("events") or []:
            try:
                if datetime.datetime.fromisoformat(e["t"]).timestamp() >= cut:
                    ev.append(e)
            except (KeyError, ValueError):
                continue
    return cost.summarize(ev)


SLUG_RE = re.compile(r"^[\w.-]{1,120}$")


def slug_ok(slug):
    return bool(SLUG_RE.match(slug)) and ".." not in slug and os.path.isdir(os.path.join(PROJECTS, slug))


def dump(obj):
    return json.dumps(obj, ensure_ascii=False)
