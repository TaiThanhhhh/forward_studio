"""Giọng đọc khác nhau cho mỗi video (vòng 7b) — kho giọng `config/voice.json → pools.<ngôn ngữ>`.

Mỗi video chọn MỘT giọng và giữ nguyên (`storyboard.voice_resolved`), chạy lại không đổi giọng, không tốn credit:
  1. `storyboard.voice` = tên ("Brian") hoặc id ElevenLabs → dùng đúng giọng đó (cờ CLI `--voice`).
  2. `"auto"` (mặc định) → bỏ giọng của `rotation.avoid_recent` video gần nhất, chấm điểm theo nhãn: giọng có nhãn trùng
     `voice_tags` của style (vd swiss-motion → formal/steady; line-boil → storyteller/playful), cộng điểm nếu khác giới
     tính với video ngay trước (đổi màu giọng giữa các ngày); hoà điểm → giọng lâu chưa dùng nhất, rồi thứ tự trong kho.
Giọng có `"auto": false` (giọng nhân vật) chỉ dùng khi chỉ định tay hoặc khi style có nhãn `character`.
Nhịp đọc: mỗi giọng nói nhanh/chậm khác nhau → `vo.py` tự tính atempo theo nhịp thật của bản TTS (xem `tempo_for`).
"""

import os

from .common import PROJECTS, channel, load_json


def cfg():
    from .tts import voice_cfg  # noqa: PLC0415

    return voice_cfg()


def pool(language=None, include_manual=False):
    from . import lang  # noqa: PLC0415

    c = cfg()
    lg = (language or lang.language() or "en")[:2]
    out = [v for v in (c.get("pools") or {}).get(lg, []) if isinstance(v, dict) and v.get("id")]
    if not _edge_mode():                     # vòng 23: giọng chỉ có trên Edge không dùng được khi đọc bằng ElevenLabs
        out = [v for v in out if v.get("provider") != "edge"]
    if not out:  # cấu hình cũ: chỉ có voice + alternates
        out = [c["voice"]] + [v for v in c.get("alternates", []) if v.get("id")]
    return [v for v in out if include_manual or v.get("auto", True)]


def _edge_mode():
    """Đang đọc bằng Edge Neural TTS? (TTS_PROVIDER=edge, hoặc không có key ElevenLabs)."""
    from .common import env  # noqa: PLC0415
    pref = (env("TTS_PROVIDER") or os.environ.get("TTS_PROVIDER") or "").strip().lower()
    return pref == "edge" or not env(cfg().get("api_key_env", "ELEVENLABS_API_KEY"))


def short(v):
    return (v.get("name") or v.get("id", "?")).split(" ")[0].split("—")[0].strip()


def find(name_or_id, language=None):
    """Giọng theo id hoặc tên (không phân biệt hoa thường, khớp tên ngắn 'Brian')."""
    if not name_or_id:
        return None
    key = str(name_or_id).strip().lower()
    for v in pool(language, include_manual=True) + [cfg()["voice"]] + cfg().get("alternates", []):
        if v.get("id", "").lower() == key or short(v).lower() == key or v.get("name", "").lower() == key:
            return {k: v[k] for k in v if not k.startswith("_")}
    return None


def history(exclude=None):
    """[(mtime, slug, voice_id)] mới nhất trước — từ storyboard.voice_resolved, hoặc audio/vo_alignment.json (video cũ)."""
    out = []
    if not os.path.isdir(PROJECTS):
        return out
    for slug in os.listdir(PROJECTS):
        if slug.startswith(("_", ".", "cmp-")) or slug == exclude:  # cmp-*: bản so sánh style, không phải video đăng
            continue
        d = os.path.join(PROJECTS, slug)
        sb = load_json(os.path.join(d, "storyboard.json"), {}) if os.path.exists(os.path.join(d, "storyboard.json")) else {}
        vid = (sb.get("voice_resolved") or {}).get("id")
        al = os.path.join(d, "audio", "vo_alignment.json")
        if not vid and os.path.exists(al):
            vid = (load_json(al, {}).get("voice") or {}).get("id")
        if not vid:
            continue
        fin = os.path.join(d, "out", "final.mp4")
        t = os.path.getmtime(fin) if os.path.exists(fin) else os.path.getmtime(al if os.path.exists(al) else d)
        out.append((t, slug, vid))
    return sorted(out, reverse=True)


def ranked(style=None, slug=None, language=None):
    """[(giọng, điểm, lý do)] — giọng tốt nhất trước (đã bỏ giọng vừa dùng nếu kho còn đủ)."""
    from . import textstyle  # noqa: PLC0415

    rot = cfg().get("rotation", {})
    n = int(rot.get("avoid_recent", 4))
    hist = history(exclude=slug)
    recent = [vid for _, _, vid in hist[:n]]
    last = hist[0][2] if hist else None
    want = []
    if style and style != "auto":
        try:
            want = [t.lower() for t in textstyle.load_style(style).get("voice_tags") or []]
        except Exception:  # noqa: BLE001
            want = []
    cands = pool(language, include_manual="character" in want)
    fresh = [v for v in cands if v["id"] not in recent] or cands
    by_id = {v["id"]: v for v in pool(language, include_manual=True)}
    last_gender = (by_id.get(last) or {}).get("gender")
    used_at = {}
    for k, (_, _, vid) in enumerate(hist):
        used_at.setdefault(vid, k)
    rows = []
    for i, v in enumerate(fresh):
        tags = {t.lower() for t in v.get("tags", [])}
        hit = [t for t in want if t in tags]
        sc = len(hit) + (0.5 if last_gender and v.get("gender") and v["gender"] != last_gender else 0)
        why = (f"hợp style ({', '.join(hit)})" if hit else "không nhãn nào trùng style") + (
            " · đổi giới tính so với video trước" if sc % 1 else ""
        )
        rows.append((v, sc, why, -used_at.get(v["id"], 10**6), i))
    rows.sort(key=lambda r: (-r[1], r[3], r[4]))
    return [(r[0], r[1], r[2]) for r in rows]


def resolve(sb, slug):
    """(giọng {id, name, …}, ghi chú|None). Ổn định: đã có voice_resolved thì giữ (trừ khi người dùng đổi `voice`)."""
    want = sb.get("voice") or "auto"
    cur = sb.get("voice_resolved") or {}
    language = sb.get("language")
    if want != "auto":
        v = find(want, language)
        if not v:
            names = ", ".join(short(x) for x in pool(language, include_manual=True))
            return None, f"không có giọng '{want}' trong config/voice.json → pools (có: {names})"
        return v, None
    if cur.get("id") and cur.get("auto_pick"):
        return cur, None
    rk = ranked(sb.get("style_resolved") or sb.get("style"), slug, language)
    if not rk:
        return dict(cfg()["voice"]), None
    v, sc, why = rk[0]
    v = {k: v[k] for k in v if not k.startswith("_")}
    v["auto_pick"] = True
    rec = [
        short(find(vid) or {"id": vid})
        for _, _, vid in history(exclude=slug)[: int(cfg().get("rotation", {}).get("avoid_recent", 4))]
    ]
    return v, f"giọng auto → {short(v)} ({why}; {len(rec)} video gần nhất: {', '.join(rec) or '—'})"


def adaptive_speed(raw_wps):
    """atempo = nhịp mục tiêu / nhịp nói thật, kẹp [speed_min, speed_max]."""
    from . import lang  # noqa: PLC0415

    vc = channel()["vo"]
    if not vc.get("speed_auto", True) or not raw_wps:
        return float(vc.get("speed") or 1.0)
    target = float(vc.get("target_wps") or lang.pace())
    return round(max(float(vc.get("speed_min", 1.0)), min(float(vc.get("speed_max", 1.18)), target / float(raw_wps))), 3)


def tempo_for(proj, sb, base):
    """atempo hậu kỳ cho video này. Video vòng 7b trở đi (có voice_resolved): đo nhịp NÓI thật của bản TTS (trước atempo)
    → atempo = nhịp mục tiêu / nhịp thật, kẹp trong [speed_min, speed_max] → giọng chậm (Brian, Charlie) hay nhanh
    đều ra cùng nhịp kênh. Video cũ: giữ vo.speed cố định (không đổi timeline của video đã đăng)."""
    from . import lang  # noqa: PLC0415

    vc = channel()["vo"]
    vr = sb.get("voice_resolved") or {}
    if not (vr and not vr.get("legacy") and vc.get("speed_auto", True)):
        return base, None
    a = load_json(os.path.join(proj, "audio", "vo_alignment.json"), {})
    raw = a.get("raw_words_per_sec")
    if not raw and a.get("words_per_sec"):
        raw = float(a["words_per_sec"]) / float(a.get("speed_at_synth") or vc.get("speed") or 1.0)
    if not raw:
        return base, None
    target = float(vc.get("target_wps") or lang.pace())
    sp = adaptive_speed(raw)
    return sp, f"atempo {sp:.3f} (giọng nói {raw:.2f} từ/giây → mục tiêu {target})"
