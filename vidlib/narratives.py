"""Dạng kịch bản (narrative) xoay vòng theo video — như style và giọng: hai video liền nhau không kể cùng một khung.

`config/narratives.json` là nguồn: mỗi dạng có `shape` (cách kể, tiếng Anh, đưa vào brief), `visual` (hình hợp dạng đó,
cho ngày code lẫn ngày Flow), `tags` (chủ đề hợp), `strong` (regex trên ý tưởng: tiêu đề "5 things…" buộc phải đếm
ngược) và `moves` (kiểu bay camera của engine html hợp dạng đó — vidlib/spine.py giao với ngữ pháp camera của look).

Chọn TRƯỚC khi viết brief (plan.json → `narrative`): bỏ dạng đã dùng trong `avoid_recent` video gần nhất (trừ dạng mà ý
tưởng bắt buộc qua `strong` hoặc idea.json → `narrative`); điểm = nhãn chủ đề khớp + 3 nếu `strong` + 4 nếu ý tưởng gợi ý +
`base` + nhiễu tất định theo slug (bằng điểm thì mỗi video một khác). Ép tay: `--narrative <id>`.
Storyboard ghi `"narrative": "<id>"`; tool ghi `narrative_resolved`. Dự án cũ (không có trường này) giữ nguyên, không đổi.
"""
import hashlib
import os
import re
from functools import cache

from . import styles
from .common import CONFIG_DIR, PROJECTS, StudioError, load_json


@cache
def config():
    return load_json(os.path.join(CONFIG_DIR, "narratives.json"))


def ids():
    return list(config()["narratives"])


def get(nid):
    return config()["narratives"].get(nid or "")


def moves(nid):
    """Kiểu bay camera spine ưa dùng cho dạng này ([] = theo look)."""
    return list((get(nid) or {}).get("moves") or [])


def history(exclude=None):
    """[(mtime, slug, narrative)] mới nhất trước — lấy từ storyboard (narrative_resolved / narrative) hoặc plan.json."""
    out = []
    if not os.path.isdir(PROJECTS):
        return out
    for slug in os.listdir(PROJECTS):
        if slug.startswith(("_", ".", "cmp-")) or slug == exclude:
            continue
        d = os.path.join(PROJECTS, slug)
        paths = [os.path.join(d, n) for n in ("out/final.mp4", "storyboard.json", "plan.json")]
        have = [p for p in paths if os.path.exists(p)]
        if not have:
            continue
        sb = load_json(paths[1], {}) if os.path.exists(paths[1]) else {}
        pl = load_json(paths[2], {}) if os.path.exists(paths[2]) else {}
        nid = sb.get("narrative_resolved") or sb.get("narrative") or pl.get("narrative")
        if nid in config()["narratives"]:
            out.append((os.path.getmtime(have[0]), slug, nid))
    return sorted(out, reverse=True)


def recent(n=None, exclude=None):
    n = n or int(config().get("avoid_recent", 3))
    return [x for _, _, x in history(exclude)[:n]]


def _jitter(seed, nid):
    return int(hashlib.sha1(f"{seed}:{nid}".encode()).hexdigest()[:6], 16) / 0xFFFFFF * 0.5


def is_strong(nid, text):
    return any(re.search(p, text, re.I) for p in (get(nid) or {}).get("strong") or [])


def score(nid, text, stems=None):
    d = get(nid) or {}
    stems = stems if stems is not None else styles._stems(text)
    tags = [t for t in d.get("tags") or [] if styles.score_tag(t, text, stems)]
    return float(d.get("base", 0)) + len(tags) + (3 if is_strong(nid, text) else 0), tags


def ranked(text, slug=None, hint=None):
    """[(id, điểm, nhãn khớp)] — bỏ dạng vừa dùng, trừ dạng ý tưởng bắt buộc (strong) hoặc gợi ý (hint)."""
    text = text.lower()
    rec = set(recent(exclude=slug))
    stems = styles._stems(text)
    seed = slug or text
    rows = []
    for nid in ids():
        if nid in rec and not is_strong(nid, text) and nid != hint:
            continue
        sc, tags = score(nid, text, stems)
        rows.append((nid, sc + (4 if nid == hint else 0) + _jitter(seed, nid), tags))
    if not rows:                          # mọi dạng vừa dùng hết (kho ít hơn avoid_recent) → nới chống lặp
        rows = [(nid, score(nid, text, stems)[0] + _jitter(seed, nid), score(nid, text, stems)[1]) for nid in ids()]
    return sorted(rows, key=lambda r: (-r[1], ids().index(r[0])))


def plan(topic, slug=None, want=None, idea=None):
    """{narrative, narrative_reason, narrative_alternatives} cho plan.json. want: --narrative; idea: idea.json."""
    if want and want != "auto":
        if want not in ids():
            raise StudioError(f"Không có dạng kịch bản '{want}' (có: {', '.join(ids())}).")
        return {"narrative": want, "narrative_reason": "chỉ định tay (--narrative)"}
    idea = idea or {}
    text = " ".join(str(x) for x in (topic, idea.get("title"), idea.get("hook")) if x)
    hint = idea.get("narrative") if idea.get("narrative") in ids() else None
    rk = ranked(text, slug, hint)
    nid, _, tags = rk[0]
    if nid == hint:
        why = "ý tưởng gợi ý dạng này (idea.json)"
    elif is_strong(nid, text.lower()):
        why = "tiêu đề/ý tưởng đòi đúng dạng này"
    elif tags:
        why = f"chủ đề khớp nhãn {', '.join(tags)}"
    else:
        why = "không nhãn nào khớp → xoay vòng"
    rec = recent(exclude=slug)
    if rec:
        why += f" · tránh lặp {len(rec)} video gần nhất: {', '.join(rec)}"
    return {"narrative": nid, "narrative_reason": why, "narrative_alternatives": [r[0] for r in rk[1:4]]}


def resolve(sb, plan=None):
    """(id|None, ghi chú|None) cho storyboard đã viết. Không có trường nào (dự án cũ) → None, giữ nguyên như trước."""
    want = sb.get("narrative")
    if want and want != "auto":
        if want in ids():
            return want, None
        return None, f"narrative '{want}' không có trong config/narratives.json (có: {', '.join(ids())}) — bỏ qua."
    p = (plan or {}).get("narrative")
    return (p, None) if p in ids() else (None, None)


def block(nid):
    """Đoạn brief §1: dạng kịch bản của video này (hoặc danh sách để LLM tự chọn khi chưa có kế hoạch)."""
    d = get(nid)
    if not d:
        shapes = "\n".join(f"  - `{k}` — {v['shape']}" for k, v in config()["narratives"].items())
        return ("**Narrative shape** — pick the ONE that fits the idea best and write its id in `\"narrative\"` "
                "(never force every video into the same template):\n" + shapes)
    return (f"**NARRATIVE SHAPE FOR THIS VIDEO:** `{nid}` — write `\"narrative\": \"{nid}\"`. The channel rotates shapes "
            "per video so no two videos in a row tell the story the same way — follow THIS one"
            + (":\n" if nid == "classic" else ", not the classic hook → escalate → payoff arc:\n")
            +
            f"  - {d['shape']}\n  - Visuals that carry it: {d['visual']}")


# ---------------------------------------------------------------------------
# Director Archetypes (Vòng 13 — config/archetypes.json)
# ---------------------------------------------------------------------------


@cache
def archetypes_config():
    return load_json(os.path.join(CONFIG_DIR, "archetypes.json"))


def archetype_ids():
    return list(archetypes_config()["archetypes"])


def get_archetype(aid):
    return archetypes_config()["archetypes"].get(aid or "")


def archetype_moves(aid):
    """Kiểu bay camera spine ưa dùng cho archetype này ([] = theo narrative/look)."""
    return list((get_archetype(aid) or {}).get("moves") or [])


def archetype_history(exclude=None):
    """[(mtime, slug, archetype)] mới nhất trước — đọc từ storyboard (archetype_resolved / archetype) hoặc plan.json."""
    out = []
    if not os.path.isdir(PROJECTS):
        return out
    valid = archetypes_config()["archetypes"]
    for slug in os.listdir(PROJECTS):
        if slug.startswith(("_", ".", "cmp-")) or slug == exclude:
            continue
        d = os.path.join(PROJECTS, slug)
        paths = [os.path.join(d, n) for n in ("out/final.mp4", "storyboard.json", "plan.json")]
        have = [p for p in paths if os.path.exists(p)]
        if not have:
            continue
        sb = load_json(paths[1], {}) if os.path.exists(paths[1]) else {}
        pl = load_json(paths[2], {}) if os.path.exists(paths[2]) else {}
        aid = sb.get("archetype_resolved") or sb.get("archetype") or pl.get("archetype")
        if aid in valid:
            out.append((os.path.getmtime(have[0]), slug, aid))
    return sorted(out, reverse=True)


def recent_archetypes(n=None, exclude=None):
    n = n or int(archetypes_config().get("avoid_recent", 4))
    return [x for _, _, x in archetype_history(exclude)[:n]]


def is_strong_archetype(aid, text):
    return any(re.search(p, text, re.I) for p in (get_archetype(aid) or {}).get("strong") or [])


def score_archetype(aid, text, stems=None):
    d = get_archetype(aid) or {}
    stems = stems if stems is not None else styles._stems(text)
    tags = [t for t in d.get("tags") or [] if styles.score_tag(t, text, stems)]
    return float(d.get("base", 0)) + len(tags) + (3 if is_strong_archetype(aid, text) else 0), tags


def ranked_archetypes(text, slug=None, hint=None):
    """[(id, điểm, nhãn khớp)] — bỏ archetype trong `avoid_recent` video gần nhất để không lặp khuôn đạo diễn."""
    text_l = (text or "").lower()
    rec_list = recent_archetypes(exclude=slug)
    rec = set(rec_list)
    last_used = rec_list[0] if rec_list else None
    stems = styles._stems(text_l)
    seed = slug or text_l
    all_ids = archetype_ids()
    rows = []
    for aid in all_ids:
        if aid in rec and aid != hint and not (is_strong_archetype(aid, text_l) and aid != last_used):
            continue
        sc, tags = score_archetype(aid, text_l, stems)
        rows.append((aid, sc + (4 if aid == hint else 0) + _jitter(seed, f"arch:{aid}"), tags))
    if not rows:
        # Mọi archetype đều nằm trong lịch sử gần → loại trừ ít nhất video sát trước để tránh lặp liên tiếp
        pool = [aid for aid in all_ids if aid != last_used] or all_ids
        for aid in pool:
            sc, tags = score_archetype(aid, text_l, stems)
            rows.append((aid, sc + _jitter(seed, f"arch:{aid}"), tags))
    return sorted(rows, key=lambda r: (-r[1], all_ids.index(r[0])))


def plan_archetype(topic, slug=None, want=None, idea=None):
    """{archetype, archetype_reason, archetype_alternatives} cho plan.json. want: --archetype; idea: idea.json."""
    all_ids = archetype_ids()
    if want and want != "auto":
        if want not in all_ids:
            raise StudioError(f"Không có archetype '{want}' (có: {', '.join(all_ids)}).")
        return {"archetype": want, "archetype_reason": "chỉ định tay (--archetype)"}
    idea = idea or {}
    text = " ".join(str(x) for x in (topic, idea.get("title"), idea.get("hook")) if x)
    hint = idea.get("archetype") if idea.get("archetype") in all_ids else None
    rk = ranked_archetypes(text, slug, hint)
    aid, _, tags = rk[0]
    if aid == hint:
        why = "ý tưởng gợi ý archetype này (idea.json)"
    elif is_strong_archetype(aid, text.lower()):
        why = "tiêu đề/ý tưởng khớp mạnh phong cách đạo diễn này"
    elif tags:
        why = f"chủ đề khớp nhãn {', '.join(tags)}"
    else:
        why = "xoay vòng phong cách đạo diễn"
    rec = recent_archetypes(exclude=slug)
    if rec:
        why += f" · tránh lặp {len(rec)} video gần nhất: {', '.join(rec)}"
    return {"archetype": aid, "archetype_reason": why, "archetype_alternatives": [r[0] for r in rk[1:4]]}


def resolve_archetype(sb, plan=None):
    """(id|None, ghi chú|None) cho storyboard đã viết. Dự án cũ không có trường này → (None, None)."""
    want = (sb or {}).get("archetype")
    if want and want != "auto":
        if want in archetype_ids():
            return want, None
        return None, (f"archetype '{want}' không có trong config/archetypes.json "
                      f"(có: {', '.join(archetype_ids())}) — bỏ qua.")
    p = (plan or {}).get("archetype")
    return (p, None) if p in archetype_ids() else (None, None)


def archetype_block(aid):
    """Đoạn brief đạo diễn (tiếng Anh) cho vidlib/brief.py: khóa 1 trong 6 Viral Director Archetypes."""
    d = get_archetype(aid)
    if not d:
        items = []
        for k, v in archetypes_config()["archetypes"].items():
            studios = " / ".join(v.get("reference_studios") or [])
            beats = ", ".join(f"`{b}`" for b in (v.get("required_beats") or []))
            items.append(
                f"  - `{k}` ({studios}; mood `{v['music_mood']}`; outro `{v['outro_mode']}`; beats {beats}): "
                f"{v['arc_rules']}"
            )
        return ("**DIRECTOR ARCHETYPE** — pick ONE viral director style that fits the idea best and write its id in "
                "`\"archetype\"` (the channel rotates across 6 distinct archetypes so consecutive shorts never feel "
                "alike):\n" + "\n".join(items))
    studios = " / ".join(d.get("reference_studios") or [])
    beats = ", ".join(f"`{b}`" for b in (d.get("required_beats") or []))
    cams = ", ".join(f"`{c}`" for c in (d.get("camera_presets") or []))
    trans = ", ".join(f"`{t}`" for t in (d.get("transitions") or []))
    outro_mode = d.get("outro_mode", "loop")
    if outro_mode == "loop":
        outro_rule = ('`"outro": {"mode": "loop", "bridge_frames": 8}` — NO static "Follow for more" card; write '
                      "the final spoken line so its grammar and thought bridge seamlessly straight back into Shot 1 "
                      "for AVD > 100%.")
    else:
        outro_rule = ('`"outro": {"mode": "code"}` with a sharp 1-line `outro.teaser` (or `"mode": "loop"` if the '
                      "closing twist loops naturally back into Shot 1).")
    hud_line = ""
    if aid in ("ticking_clock", "visceral_anatomy"):
        hud_line = ("\n  - **Persistent `story_hud`:** include a top-level `story_hud` "
                    "(`{\"kind\": \"clock|temp|bpm|meter\", \"label\": \"...\", \"from\": ..., \"to\": ..., "
                    "\"unit\": \"...\", \"role\": \"hot|accent\"}`) so escalating telemetry stays locked in Zone A "
                    "across shots.")
    return (
        f"**DIRECTOR ARCHETYPE FOR THIS VIDEO:** `{aid}` ({studios}) — write `\"archetype\": \"{aid}\"`. "
        "Direct every beat, camera angle, transition, and pacing choice in THIS studio voice:\n"
        f"  - **Arc Blueprint:** {d['arc_rules']}\n"
        f"  - **Signature Visual Beats:** {beats}\n"
        f"  - **3D Camera Presets (`stage` `frame.preset`):** {cams} (alternate angles — never repeat `diorama`)\n"
        f"  - **Agency Transitions (`transition_in`):** {trans}\n"
        f"  - **Audio Identity (`music_mood`):** `{d['music_mood']}`\n"
        f"  - **Ending:** {outro_rule}{hud_line}"
    )
