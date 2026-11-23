"""Thư viện của tool cho UI: style, giọng, dạng kịch bản, stage, kế hoạch (style + giọng + khung kể) cho một ý tưởng.
Mọi dữ liệu đọc từ vidlib (một nguồn sự thật) — UI không giữ bản sao cấu hình."""
import functools
import os

from vidlib import narratives, pipeline, styles, textstyle, voices
from vidlib.common import ROOT

ENGINE_LABEL = {"flow": "Google Flow", "three": "3D three.js", "html": "Motion 2D (html)", "manim": "Sơ đồ Manim",
                "board": "Evidence board"}


def _preview(sid):
    """Ảnh xem trước có sẵn của style (sinh bởi scripts/props3d_sheet.py, html_sheet.py, styles --gallery)."""
    for root, rel in (("qa", f"props3d/{sid}.jpg"), ("qa", f"html/{sid}.jpg"), ("qa", f"styles/{sid}.jpg"),
                      ("qa", f"icons/{sid}.jpg")):
        if os.path.exists(os.path.join(ROOT, root, rel)):
            return {"root": root, "path": rel}
    return None


def style_list():
    hist = styles.history()
    last = {}
    for _, slug, st in reversed(hist):
        last[st] = slug
    out = []
    for sid in styles.available():
        st = textstyle.load_style(sid)
        info = styles.info(sid)
        pal = st.get("palette") or (st.get("html") or {}).get("palette") or {}
        world = st.get("world") or {}
        lk = world.get("look3d")
        out.append({
            "id": sid, "name": info["name"], "description": info["description"], "engine": info["engine"],
            "engine_label": ENGINE_LABEL.get(info["engine"], info["engine"]), "code_only": info["code_only"],
            "uses_flow": styles.uses_flow(sid), "tags": info["tags"], "assembly": info["assembly"],
            "palette": {k: v for k, v in pal.items() if isinstance(v, str) and v.startswith("#")},
            "look3d": (lk if isinstance(lk, str) else (lk or {}).get("kind")) if lk else None,
            "html_look": (st.get("html") or {}).get("look"), "font": st.get("font"),
            "is_3d": bool((st.get("flow") or {}).get("is_3d")) or bool(lk), "special": info["special"],
            "ready": styles.engine_ready(sid), "last_used": last.get(sid), "preview": _preview(sid),
            "card": f"{sid}.md" if os.path.exists(os.path.join(ROOT, "styles", f"{sid}.md")) else None,
            "category": info.get("category") or "", "category_name": st.get("category_name") or "",
            "tier": info.get("tier"), "brand_fit": info.get("brand_fit"), "auto": info.get("auto", True),
            "atlas": (st.get("atlas") or {}).get("number"), "duplicate_of": (st.get("atlas") or {}).get("duplicate_of"),
            "frame": f"styles/{sid}.jpg" if os.path.exists(os.path.join(ROOT, "qa", "styles", f"{sid}.jpg")) else None,
        })
    return out


def voice_list():
    used = {}
    for _, slug, vid in reversed(voices.history()):
        used[vid] = slug
    out = []
    for v in voices.pool(include_manual=True):
        out.append({"id": v["id"], "short": voices.short(v), "name": v.get("name", ""), "gender": v.get("gender", ""),
                    "accent": v.get("accent", ""), "tags": v.get("tags", []), "auto": v.get("auto", True),
                    "last_used": used.get(v["id"])})
    return out


def narrative_list(topic=""):
    used = {}
    for _, slug, nid in reversed(narratives.history()):
        used[nid] = slug
    scores = {r[0]: r[1] for r in narratives.ranked(topic)} if topic else {}
    ids = [r[0] for r in narratives.ranked(topic)] if topic else narratives.ids()
    out = []
    for nid in ids:
        d = narratives.get(nid)
        out.append({"id": nid, "name": d.get("name", nid), "shape": d.get("shape", ""), "tags": d.get("tags", []),
                    "score": scores.get(nid), "last_used": used.get(nid)})
    return {"items": out, "recent": narratives.recent()}


def plan(topic, flow=None, style=None, narrative=None):
    """Như `studio.py styles --plan`: style + giọng + dạng kịch bản cho một ý tưởng (không ghi file)."""
    pl = styles.plan(topic, flow=flow, style=style or None)
    v, why = voices.resolve({"voice": "auto", "style_resolved": pl["style"], "language": "en"}, None)
    pl["voice"] = {"short": voices.short(v), "name": v.get("name", ""), "gender": v.get("gender", ""),
                   "tags": v.get("tags", [])} if v else None
    pl["voice_reason"] = why
    pl.update(narratives.plan(topic, want=narrative or None))
    nid = pl.get("narrative")
    if nid:
        pl["narrative_name"] = narratives.get(nid).get("name", nid)
    pl["style_name"] = textstyle.load_style(pl["style"]).get("name", pl["style"])
    pl["engine_label"] = ENGINE_LABEL.get(pl.get("engine"), pl.get("engine"))
    return pl


@functools.lru_cache(maxsize=1)
def stages():
    return {"stages": pipeline.STAGES, "exit": pipeline.EXIT}


ROUND10_STYLES = (
    "retro90-lowpoly-black", "halftone-print-black", "vintage-comic-black",
    "pixel16-black", "sprite8-black", "ink-silhouette-black", "paper-cutout-black",
)


def schema():
    """Schema động từ các engine + kho Vòng 10 cho Properties Panel (Board) và tab Kho Vòng 10 (Library)."""
    from engines import adapter, html  # noqa: PLC0415

    beats = {}
    for b, (req, doc) in html.PARAMS.items():
        beats[b] = {
            "required": list(req),
            "doc": doc,
            "layouts": list(html.LAYOUTS.get(b, ())),
            "layout_help": getattr(html, "LAYOUT_HELP", {}).get(b, {}),
        }
    try:
        creatures3d = adapter.creature_vocab()
    except Exception:  # noqa: BLE001
        creatures3d = {}
    try:
        rig2d = html.rig_vocab() or {}
    except Exception:  # noqa: BLE001
        rig2d = {}
    try:
        from vidlib import assets3d  # noqa: PLC0415
        a_sum = assets3d.summary()
        a_models = [
            {"name": n, "group": e.get("group", ""), "pack": e.get("pack", ""),
             "anims": [a["name"] if isinstance(a, dict) else str(a) for a in (e.get("anims") or [])],
             "tags": (e.get("tags") or [])[:6]}
            for n, e in list((assets3d.models() or {}).items())[:250]
        ]
    except Exception:  # noqa: BLE001
        a_sum, a_models = {}, []
    try:
        from lib import motion  # noqa: PLC0415
        verbs = getattr(motion, "VERBS", {})
        verb_doc = getattr(motion, "VERB_DOC", {})
        staggers = list(getattr(motion, "STAGGERS", ()))
    except Exception:  # noqa: BLE001
        verbs, verb_doc, staggers = {}, {}, []
    try:
        from vidlib import motionplan  # noqa: PLC0415
        mets = [
            {"id": m.get("id"), "keywords": (m.get("keywords") or [])[:8], "mechanism": m.get("mechanism"),
             "recipe": m.get("recipe"), "verbs": m.get("verbs") or [], "avoid": m.get("avoid")}
            for m in motionplan.metaphors()
        ]
    except Exception:  # noqa: BLE001
        mets = []
    try:
        three_scenes = adapter.get("three").scenes()
    except Exception:  # noqa: BLE001
        three_scenes = ["stage"]
    all_styles = style_list()
    r10_styles = [s for s in all_styles if s["id"] in ROUND10_STYLES]
    return {
        "beats": beats,
        "layouts": {k: list(v) for k, v in html.LAYOUTS.items()},
        "html_looks": list(getattr(html, "LOOKS", ())),
        "three_scenes": three_scenes,
        "creatures3d": creatures3d,
        "rig2d": rig2d,
        "assets3d": {"summary": a_sum, "models": a_models},
        "verbs": verbs,
        "verb_doc": verb_doc,
        "staggers": staggers,
        "metaphors": mets,
        "round10_styles": r10_styles,
    }

