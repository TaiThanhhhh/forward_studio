"""Kiểm tra môi trường + tóm tắt cấu hình cho trang Cài đặt. Không bao giờ trả về giá trị API key — chỉ có/không."""
import os
import platform
import shutil
import subprocess

from vidlib.common import ROOT, channel, env, ffbin, save_text

ENV_KEYS = ("ELEVENLABS_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")
ENV_PATH = os.path.join(ROOT, ".env")


def _git_branch():
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                           timeout=3, check=False)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _browser():
    for name in ("msedge", "chrome", "chromium", "google-chrome"):
        p = shutil.which(name)
        if p:
            return p
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if os.path.exists(p):
            return p
    return None


def checks():
    out = []

    def add(key, label, ok, detail="", level="error"):
        out.append({"key": key, "label": label, "ok": bool(ok), "detail": detail, "level": "ok" if ok else level})

    try:
        add("ffmpeg", "ffmpeg", True, ffbin("ffmpeg"))
    except Exception as e:  # noqa: BLE001
        add("ffmpeg", "ffmpeg", False, str(e))
    b = _browser()
    add("browser", "Edge/Chromium (engine three.js + html)", b, b or "Không thấy — engine code-shot cần Edge/Chromium")
    try:
        from engines import manim  # noqa: PLC0415
        add("manim", "Manim CE (style physics-diagram)", manim.available(), "pip install manim", level="warn")
    except Exception as e:  # noqa: BLE001
        add("manim", "Manim CE", False, str(e), level="warn")
    for k, lab, lvl in (("ELEVENLABS_API_KEY", "ElevenLabs (giọng đọc)", "warn"),
                        ("ANTHROPIC_API_KEY", "Anthropic API (--ai claude)", "info"),
                        ("GEMINI_API_KEY", "Gemini API (--ai gemini)", "info")):
        add(k, lab, env(k), "có trong .env / biến môi trường" if env(k) else "chưa có (tuỳ chọn)", level=lvl)
    return out


def config_summary():
    c = channel()
    st = c.get("styles", {})
    cr = c.get("code_render", {})
    return {
        "channel": c.get("name"), "language": c.get("language"), "ui_language": c.get("ui_language"),
        "format": c.get("format_label") or c.get("format"), "wps": (c.get("script") or {}).get("wps"),
        "style_default": st.get("default"), "flow_share": st.get("flow_share"), "balance_window": st.get("balance_window"),
        "avoid_recent": st.get("avoid_recent"), "html_workers": cr.get("html_workers"), "gpu": cr.get("gpu"),
        "python": platform.python_version(), "platform": platform.platform(terse=True), "branch": _git_branch(),
        "root": ROOT,
    }


def save_env(body, path=None):
    """Ghi API key vào .env cục bộ (chỉ 3 key cho phép). Chuỗi rỗng = giữ nguyên; clear=[key] = xoá key.
    Không bao giờ trả về giá trị key — chỉ trả trạng thái checks()."""
    if not isinstance(body, dict):
        raise ValueError("Body phải là object JSON.")
    p = path or ENV_PATH
    keys_in = body.get("keys") if isinstance(body.get("keys"), dict) else {
        k: v for k, v in body.items() if k != "clear"
    }
    clear_set = set(body.get("clear") or [])
    for k in set(keys_in) | clear_set:
        if k not in ENV_KEYS:
            raise ValueError(f"Chỉ cho phép đặt: {', '.join(ENV_KEYS)} (nhận '{k}').")
    updates = {}
    for k, v in keys_in.items():
        if v is None:
            continue
        if not isinstance(v, str):
            raise ValueError(f"Giá trị của {k} phải là chuỗi.")
        s = v.strip()
        if any(ord(c) < 32 or ord(c) == 127 for c in s):
            raise ValueError(f"Giá trị của {k} chứa ký tự điều khiển không hợp lệ.")
        if s:
            updates[k] = s
    lines = []
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    out, seen = [], set()
    for ln in lines:
        k, eq, _ = ln.strip().partition("=")
        k = k.strip()
        if eq and k in ENV_KEYS:
            seen.add(k)
            if k in clear_set and k not in updates:
                continue
            if k in updates:
                out.append(f"{k}={updates[k]}")
                continue
        out.append(ln)
    for k in ENV_KEYS:
        if k in updates and k not in seen:
            out.append(f"{k}={updates[k]}")
    save_text(p, "\n".join(out).rstrip("\n") + ("\n" if out else ""))
    return {"ok": True, "updated": sorted(set(updates) | clear_set), "checks": checks()}

