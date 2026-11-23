"""Version render v001, v002… + manifest + nguồn gốc (AUD-1101/1102/604/1107).

Sau mỗi lần render qua được cổng QA:
  out/versions/vNNN/final.mp4 (hard link nếu được, không thì copy) · thumbnails/ · publish.md · manifest.json
  out/manifest.json = bản mới nhất · out/provenance.json = thành phần AI + nhãn theo nền tảng.
Version mới chỉ tạo khi hash của final.mp4 khác bản gần nhất (chạy lại y hệt không sinh v rác).
Manifest ghi: commit SHA (+ cờ dirty), phiên bản tool, style/giọng/dạng kịch bản/model Flow, seed, engine_rev, phiên bản
ffmpeg/Python/thư viện, hash mọi đầu ra, kết quả QA, chi phí.
"""
import datetime
import glob
import hashlib
import importlib.metadata
import os
import platform
import re
import shutil
import subprocess

from .common import ROOT, ffbin, load_json, save_json

TOOL_VERSION = "3.7.0"


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def git_info():
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                             timeout=10).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True,
                                    text=True, timeout=10).stdout.strip())
        br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                            timeout=10).stdout.strip()
        return {"commit": sha or None, "dirty": dirty, "branch": br or None}
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "dirty": None, "branch": None}


def tool_versions():
    out = {"tool": TOOL_VERSION, "python": platform.python_version(), "os": platform.platform(terse=True)}
    try:
        r = subprocess.run([ffbin("ffmpeg"), "-version"], capture_output=True, text=True, timeout=20)
        out["ffmpeg"] = (r.stdout.splitlines() or [""])[0].replace("ffmpeg version ", "").split(" Copyright")[0]
    except (OSError, subprocess.SubprocessError):
        out["ffmpeg"] = None
    for pkg in ("pillow", "numpy", "opencv-python", "playwright", "manim"):
        try:
            out[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            out[pkg] = None
    return out


def versions_dir(proj):
    return os.path.join(proj, "out", "versions")


def latest(proj):
    vs = sorted(glob.glob(os.path.join(versions_dir(proj), "v[0-9][0-9][0-9]")))
    return vs[-1] if vs else None


def _link_or_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        if os.path.exists(dst):
            os.remove(dst)
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def build(proj, sb, plan=None, qa=None, cost=None, engine_rev=None, extra=None):
    """Manifest (dict) cho trạng thái hiện tại của out/."""
    final = os.path.join(proj, "out", "final.mp4")
    outs = {}
    for p in [final, *glob.glob(os.path.join(proj, "out", "*.srt")), os.path.join(proj, "publish.md"),
              *glob.glob(os.path.join(proj, "thumbnails", "*.png")), *glob.glob(os.path.join(proj, "thumbnails", "*.jpg")),
              *glob.glob(os.path.join(proj, "out", "deliver", "*", "video.mp4"))]:
        if os.path.exists(p):
            outs[os.path.relpath(p, proj).replace("\\", "/")] = {"sha256": sha256(p), "bytes": os.path.getsize(p)}
    shots = sb.get("shots") or []
    return {
        "schema": 1, "created": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "project": os.path.basename(proj), "title": sb.get("title") or sb.get("topic"),
        "style": sb.get("style_resolved") or sb.get("style"), "voice": (plan or {}).get("voice") or sb.get("voice"),
        "narrative": (plan or {}).get("narrative") or sb.get("narrative"),
        "flow_models": {k: (sb.get("flow") or {}).get(k) for k in ("video_model", "image_model")},
        "modes": {s["id"]: s.get("mode_resolved") or s.get("mode") for s in shots},
        "seed": sb.get("seed"), "engine_rev": engine_rev, "git": git_info(), "versions": tool_versions(),
        "qa": qa, "cost": cost, "outputs": outs, **(extra or {}),
    }


def write(proj, sb, **kw):
    """Ghi out/manifest.json + tạo version mới nếu final.mp4 đổi. Trả về (tên version, manifest)."""
    m = build(proj, sb, **kw)
    final = os.path.join(proj, "out", "final.mp4")
    if not os.path.exists(final):
        save_json(os.path.join(proj, "out", "manifest.json"), m)
        return None, m
    cur = m["outputs"].get("out/final.mp4", {}).get("sha256")
    last = latest(proj)
    if last and load_json(os.path.join(last, "manifest.json"), {}).get("outputs", {}).get("out/final.mp4", {}).get(
            "sha256") == cur:
        m["version"] = os.path.basename(last)
    else:
        n = int(re.sub(r"\D", "", os.path.basename(last))) + 1 if last else 1
        vdir = os.path.join(versions_dir(proj), f"v{n:03d}")
        _link_or_copy(final, os.path.join(vdir, "final.mp4"))
        for rel in m["outputs"]:
            if rel.startswith(("thumbnails/", "publish.md", "out/captions")):
                _link_or_copy(os.path.join(proj, rel), os.path.join(vdir, rel.replace("out/", "")))
        m["version"] = f"v{n:03d}"
        save_json(os.path.join(vdir, "manifest.json"), m)
    save_json(os.path.join(proj, "out", "manifest.json"), m)
    return m["version"], m


def metadata_tags(sb, ai):
    """Metadata MP4 (AUD-604): mô tả nguồn gốc máy đọc được — không thay C2PA (cần chứng chỉ, chờ chủ kênh quyết định)."""
    comps = ", ".join(ai.get("components") or []) or "code-rendered animation"
    return {"title": sb.get("title") or sb.get("topic") or "", "comment": f"AI-assisted: {comps}. Edited and rendered "
            f"with studio {TOOL_VERSION}.", "description": ai.get("description_line") or "",
            "encoded_by": f"studio {TOOL_VERSION}"}
