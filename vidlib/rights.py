"""Sổ quyền (rights/ledger.json) + kiểm quyền theo từng video (AUD-601/609) + nhãn AI theo nền tảng (AUD-1201).

`usage(proj, sb)` liệt kê asset mà video thật sự dùng (font của style, SFX, nhạc, giọng, clip Flow, nguồn style);
`checks(...)` → dòng cổng QA: commercial "no" → đỏ (chặn), "unknown"/quyết định chưa chốt → vàng.
"""
import fnmatch
import glob
import os

from .common import ROOT, load_json, save_json

LEDGER = os.path.join(ROOT, "rights", "ledger.json")


def ledger():
    return load_json(LEDGER, {"assets": [], "decisions": {}})


def entry(aid):
    return next((a for a in ledger()["assets"] if a["id"] == aid), None)


def commercial(a):
    """yes | no | unknown — giải quyết 'decision:<khoá>' theo rights/ledger.json → decisions."""
    c = (a or {}).get("commercial", "unknown")
    if isinstance(c, str) and c.startswith("decision:"):
        v = str(ledger().get("decisions", {}).get(c.split(":", 1)[1], "unknown")).lower()
        if v in ("paid", "creator", "pro", "scale", "business", "ultra", "yes", "approved", "owned", "mit"):
            return "yes"
        if v in ("free", "no", "rejected"):
            return "no"
        return "unknown"
    return c


def font_entry(fname):
    for a in ledger()["assets"]:
        if a["id"].startswith("font:") and fnmatch.fnmatch(os.path.basename(fname), os.path.basename(a["path"])):
            return a
    return None


def usage(proj, sb, style=None):
    """[(asset id, lý do)] mà video này dùng."""
    from . import textstyle  # noqa: PLC0415

    out = []
    style = style or sb.get("style_resolved") or sb.get("style")
    try:
        st = textstyle.load_style(style) if style and style != "auto" else {}
    except Exception:  # noqa: BLE001
        st = {}
    for f in {st.get("font"), (st.get("html") or {}).get("font")} - {None}:
        a = font_entry(f)
        out.append((a["id"] if a else f"font:?{f}", f"font của style `{style}`"))
    src = (st.get("source") or {}).get("repo", "")
    for a in ledger()["assets"]:
        if a["id"].startswith("style:") and a["source"].split(" ")[0].split("/")[-1].lower() in src.lower():
            out.append((a["id"], f"nguồn style `{style}`"))
    if st.get("atlas"):
        out.append(("style:3d-style-atlas", f"style `{style}` chuyển từ 3D Style Atlas"))
    out.append(("sfx:builtin", "SFX tổng hợp"))
    user_sfx = [p for p in glob.glob(os.path.join(ROOT, "assets", "sfx", "*.wav"))]
    if user_sfx:
        out.append(("sfx:user", f"{len(user_sfx)} file SFX người dùng trong assets/sfx/"))
    music = glob.glob(os.path.join(proj, "audio", "music.*"))
    out.append(("music:user", os.path.basename(music[0])) if music else ("music:synth", "nhạc tổng hợp"))
    if glob.glob(os.path.join(proj, "audio", "vo.mp3")):
        out.append(("voice:elevenlabs", "lời đọc ElevenLabs"))
    clips = [p for p in glob.glob(os.path.join(proj, "clips", "*")) if os.path.isfile(p)]
    if clips:
        out.append(("clip:flow", f"{len(clips)} clip Google Flow"))
    seen, uniq = set(), []
    for aid, why in out:
        if aid not in seen:
            seen.add(aid)
            uniq.append((aid, why))
    return uniq


def checks(use, dry=False):
    """Dòng cổng QA cho quyền sử dụng (nhãn 'quyền …')."""
    rows = {}
    for aid, why in use:
        a = entry(aid)
        if not a:
            rows[f"quyền: {aid}"] = (f"{why} — chưa có trong rights/ledger.json", None)
            continue
        c = commercial(a)
        if dry and aid in ("voice:elevenlabs", "clip:flow"):
            c = "yes"                                # dry-run dùng dữ liệu giả, không phải asset thật
        label = f"quyền: {aid}" if c != "no" else f"quyền thương mại BỊ CẤM: {aid}"
        rows[label] = (f"{why} · {a['license']}" + (f" · {a['note']}" if a.get("note") else ""),
                       True if c == "yes" else (False if c == "no" else None))
    return rows


def ai_disclosure(use):
    """Nhãn AI theo nền tảng (YouTube / TikTok / Meta), theo bảng chính sách tra cứu 15/11/2026."""
    ids = {a for a, _ in use}
    flow, voice = "clip:flow" in ids, "voice:elevenlabs" in ids
    if flow:
        need = {"youtube": "BẮT BUỘC (clip AI trông như thật)", "tiktok": "BẮT BUỘC", "instagram": "BẮT BUỘC"}
    elif voice:
        need = {"youtube": "không bắt buộc (hoạt hình rõ ràng) — vẫn ghi 'AI voice' trong mô tả",
                "tiktok": "nên bật (giọng AI nghe như thật)", "instagram": "nên bật (giọng AI nghe như thật)"}
    else:
        need = {"youtube": "không bắt buộc", "tiktok": "không bắt buộc", "instagram": "không bắt buộc"}
    parts = (["Google Flow (video)"] if flow else []) + (["ElevenLabs (voice)"] if voice else [])
    return {"components": parts, "need": need,
            "description_line": ("Made with AI tools: " + ", ".join(parts) + ".") if parts else ""}


def write_project(proj, sb, dry=False):
    use = usage(proj, sb)
    rows = checks(use, dry)
    rep = {"usage": [{"id": a, "why": w} for a, w in use], "ai": ai_disclosure(use),
           "rows": [{"label": k, "value": v, "ok": ok} for k, (v, ok) in rows.items()]}
    save_json(os.path.join(proj, "out", "rights.json"), rep)
    return rep, rows
