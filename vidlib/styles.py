"""Thư viện style (styles/*.json) + chọn style theo chủ đề + chống lặp style giữa các video.

Mỗi style có: kiểu chữ text_fx (font, nét, intro…), `world` (engine three.js), `html` (engine html), `tags` (chủ đề hợp),
`voice_tags` (giọng hợp), và tuỳ chọn `code_only` (toàn bộ video dựng bằng code, không cần Flow).
storyboard.style = "auto" → `plan()` chọn TRƯỚC khi viết kịch bản: style chưa dùng trong `avoid_recent` video gần nhất,
điểm = nhãn chủ đề khớp + cân bằng ngày có Flow / ngày toàn code (`flow_share`). Ép tay: --style, --flow, --no-flow.
Chỉ định tay một style vừa dùng → cảnh báo (không chặn).
"""
import os
import re

from . import textstyle
from .common import PROJECTS, channel, load_json

# Thứ tự ưu tiên khi style = "auto" (bỏ qua style đã dùng trong avoid_recent video gần nhất). Style board (vòng 6) xen kẽ
# với style cắt cảnh để kênh không lặp một kiểu ghép; silent-film-black để cuối (hợp video có đoạn lịch sử).
PREFERENCE = ["forward", "board-black", "flat-vector-black", "chalk", "swiss-motion-black", "comic", "lab-notebook-black",
              "hud-black", "blueprint", "toon3d-lab", "clay3d-black", "line-boil-black", "chalk-case-black", "scale-zoom-black", "neon",
              "sticker-explainer-black", "ink", "isometric-black", "paper_cutout", "flowchart-black", "pictogram-black",
              "physics-diagram-black", "spy-titles-black", "sketchnote-black", "synthwave-black", "silent-film-black",
              "gallery-pointillist-black",
              # vòng 8: look 3D của engine three.js (world.look3d) — xen vào cuối, vòng chọn theo chủ đề vẫn ưu tiên nhãn
              "xray3d-black", "plastic-toy3d-black", "hologram3d-black", "lowpoly3d-black", "papercraft3d-black",
              "glass3d-black", "chrome3d-black",
              # vòng 10: 90s low poly + bộ style viral trên sân khấu đen
              "retro90-lowpoly-black", "halftone-print-black", "vintage-comic-black", "pixel16-black",
              "sprite8-black", "ink-silhouette-black", "paper-cutout-black"]


def available():
    names = textstyle.list_styles()
    return [s for s in PREFERENCE if s in names] + [s for s in names if s not in PREFERENCE]


def info(name):
    st = textstyle.load_style(name)
    return {"id": name, "name": st.get("name", name), "code_only": bool(st.get("code_only")), "has_world": "world" in st,
            "description": st.get("description", ""), "assembly": st.get("assembly") or "cuts",
            "engine": engine(name), "tags": list(st.get("tags") or []), "special": bool(st.get("special")),
            "source": (st.get("source") or {}).get("repo", ""), "category": st.get("category") or "",
            "tier": st.get("tier"), "brand_fit": st.get("brand_fit") or "ok", "variant": st.get("variant") or "",
            "auto": auto_ok(name)}


def auto_ok(name):
    """Style có vào vòng chọn tự động không: preset atlas off-brand hoặc tier ngoài `config/atlas.json → auto_tiers`
    chỉ chọn tay (--style); style khác luôn được."""
    from . import atlas  # noqa: PLC0415
    return atlas.auto_ok(textstyle.load_style(name))


def engine(name):
    """Engine chính của style: flow | three | board | html | manim (để hiển thị và để chọn engine cho shot code)."""
    st = textstyle.load_style(name)
    if st.get("code_engine"):
        return st["code_engine"]
    if (st.get("assembly") or "") == "board_spine":
        return "board"
    return "three" if st.get("code_only") else "flow"


def topic_text(sb):
    return " ".join(str(sb.get(k) or "") for k in ("topic", "title", "hook", "idea")).lower()


def _stems(text):
    """Từ của chủ đề + dạng gốc thô (sleeping → sleep, burned → burn, cells → cell, boxes → box)."""
    out = set()
    for w in re.findall(r"[a-z0-9°]+", text.lower()):
        out.add(w)
        for suf, keep in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                b = w[: len(w) - len(suf)] + keep
                out.add(b)
                if len(b) > 3 and b[-1] == b[-2]:          # stopping → stopp → stop
                    out.add(b[:-1])
                out.add(b + "e")                           # making → mak → make
    return out


def score_tag(tag, text, stems=None):
    stems = stems if stems is not None else _stems(text)
    return all(p in stems for p in tag.lower().split("-"))


def score(name, text):
    """Mức hợp chủ đề: số nhãn (`tags` trong styles/<id>.json) xuất hiện trong chủ đề (so cả dạng gốc của từ). Nhãn nhiều từ
    viết bằng gạch nối (how-big) được 2 điểm. Vd scale-zoom → kích thước; physics-diagram → nhiệt/lực; hud → không gian."""
    stems = _stems(text)
    return sum((2 if "-" in t else 1) for t in textstyle.load_style(name).get("tags") or [] if score_tag(t, text, stems))


def engine_ready(name):
    """Engine của style dùng được trên máy này (vd Manim chưa cài → không tự chọn physics-diagram-black)."""
    if engine(name) == "manim":
        from engines import manim  # noqa: PLC0415
        return manim.available()
    return True


def uses_flow(name):
    """Style có dùng clip Google Flow (ngày "có Flow") hay dựng toàn bộ bằng code (ngày "không Flow")."""
    return not textstyle.load_style(name).get("code_only")


def _balance(slug=None):
    """(tỉ lệ video dùng Flow trong balance_window video gần nhất, số video) — để cân hai loại ngày."""
    c = channel().get("styles", {})
    hist = [st for _, _, st in history(exclude=slug)[: int(c.get("balance_window", 6))] if st in available()]
    if not hist:
        return None, 0
    return sum(uses_flow(st) for st in hist) / len(hist), len(hist)


def ranked(sb, slug=None, flow=None):
    """[(style, điểm)] cho style='auto': bỏ style vừa dùng + style `special`; flow=True/False lọc ngày có/không Flow.
    Điểm = số nhãn chủ đề khớp + điểm cân bằng (loại đang thiếu so với styles.flow_share được +0.75)."""
    rec = recent(exclude=slug)
    text = topic_text(sb)
    names = available()
    c = channel().get("styles", {})
    share, n = _balance(slug)
    want_flow = float(c.get("flow_share", 0.5))
    pool = [s for s in names if s not in rec and not info(s)["special"] and auto_ok(s) and engine_ready(s)
            and (not info(s)["code_only"] or sb.get("allow_code_only", True))
            and (flow is None or uses_flow(s) == bool(flow))]
    if not pool and flow is not None:                  # mọi style loại đó vừa dùng hết → nới chống lặp, giữ ràng buộc Flow
        pool = [s for s in names if not info(s)["special"] and auto_ok(s) and engine_ready(s) and uses_flow(s) == bool(flow)]

    def bonus(s):
        if share is None or flow is not None:
            return 0.0
        if share < want_flow - 1e-9:
            return 0.75 if uses_flow(s) else 0.0
        if share > want_flow + 1e-9:
            return 0.0 if uses_flow(s) else 0.75
        return 0.0
    return sorted(((s, score(s, text) + bonus(s)) for s in pool), key=lambda x: (-x[1], names.index(x[0])))


def plan(topic, slug=None, flow=None, style=None):
    """Chọn style cho một ý tưởng TRƯỚC khi viết kịch bản (để kịch bản biết hôm nay có Flow hay toàn code).
    style: ép tay (cờ --style). flow: True = chỉ style dùng Flow, False = chỉ style toàn code (cờ --flow/--no-flow)."""
    sb = {"topic": topic}
    if style and style != "auto":
        if style not in available():
            from .common import StudioError  # noqa: PLC0415
            raise StudioError(f"Không có style '{style}' (có: {', '.join(available())}).")
        return {"style": style, "reason": "chỉ định tay (--style)", "uses_flow": uses_flow(style), "engine": engine(style)}
    rk = ranked(sb, slug, flow)
    if not rk:
        rk = [(available()[0], 0)]
    pick, sc = rk[0]
    share, n = _balance(slug)
    tags = [t for t in (textstyle.load_style(pick).get("tags") or []) if score_tag(t, topic)]
    why = (f"chủ đề khớp nhãn {', '.join(tags)}" if tags else "không nhãn nào khớp chủ đề")
    if share is not None and flow is None:
        why += f" · {round(share * n)}/{n} video gần nhất dùng Flow (mục tiêu {channel().get('styles', {}).get('flow_share', 0.5):.0%})"
    if flow is not None:
        why += " · ép " + ("ngày có Flow (--flow)" if flow else "ngày toàn code (--no-flow)")
    return {"style": pick, "reason": why, "uses_flow": uses_flow(pick), "engine": engine(pick),
            "alternatives": [s for s, _ in rk[1:5]]}


def history(exclude=None):
    """[(mtime, slug, style)] mới nhất trước — dựa trên storyboard.json của các dự án đã có final.mp4 hoặc storyboard."""
    out = []
    if not os.path.isdir(PROJECTS):
        return out
    for slug in os.listdir(PROJECTS):
        if slug.startswith(("_", ".", "cmp-")) or slug == exclude:   # cmp-*: bản so sánh style, không phải video đăng
            continue
        sp = os.path.join(PROJECTS, slug, "storyboard.json")
        if not os.path.exists(sp):
            continue
        fin = os.path.join(PROJECTS, slug, "out", "final.mp4")
        t = os.path.getmtime(fin) if os.path.exists(fin) else os.path.getmtime(sp)
        sb = load_json(sp, {})
        out.append((t, slug, sb.get("style_resolved") or sb.get("style") or "forward"))
    return sorted(out, reverse=True)


def recent(n=None, exclude=None):
    n = n or channel().get("styles", {}).get("avoid_recent", 3)
    return [s for _, _, s in history(exclude)[:n]]


def resolve(sb, slug):
    """(style, ghi chú|None). 'auto' → style đầu tiên theo PREFERENCE chưa nằm trong N video gần nhất."""
    want = sb.get("style") or channel().get("styles", {}).get("default", "auto")
    rec = recent(exclude=slug)
    names = available()
    if want == "auto":
        if sb.get("style_resolved") in names:          # đã chọn ở lần chạy trước → giữ ổn định
            return sb["style_resolved"], None
        rk = ranked(sb, slug)
        pick, sc = rk[0] if rk else (names[0], 0)
        why = f"hợp chủ đề {sc} nhãn" if sc else "không nhãn nào khớp chủ đề → theo thứ tự xoay vòng"
        return pick, f"style auto → '{pick}' ({why}; 3 video gần nhất dùng: {', '.join(rec) or '—'})"
    if want not in names:
        return want, None  # validate() sẽ báo lỗi
    if want in rec:
        return want, f"style '{want}' đã dùng trong {len(rec)} video gần nhất ({', '.join(rec)}) — cân nhắc đổi để khỏi lặp."
    return want, None


def card_md(name):
    """Thẻ style dạng Markdown, sinh từ styles/<id>.json (JSON là nguồn sự thật; chạy `python studio.py styles --cards`)."""
    st = textstyle.load_style(name)
    src, pal, pc, mk, fl, mu = (st.get(k) or {} for k in ("source", "palette", "pacing", "marks", "flow", "music"))
    L = [f"# {st.get('name', name)} (`{name}`)", "", st.get("description", ""), "",
         f"- **Engine:** `{engine(name)}`" + (" · toàn bộ bằng code (không cần Flow)" if st.get("code_only") else "")
         + (" · **tập đặc biệt** (không vào vòng xoay auto)" if st.get("special") else ""),
         *([f"- **3D Style Atlas:** #{st['atlas']['number']:02d} {st['atlas']['name']} · nhóm {st.get('category_name', '')}"
            f" · tier {st.get('tier')} · brand_fit `{st.get('brand_fit')}` · hợp kênh {st['atlas']['fit']}/5"
            + (f" · gần `{st['atlas']['duplicate_of']}`" if st['atlas'].get('duplicate_of') else "")
            + ("" if auto_ok(name) else " · **chỉ chọn tay** (không vào vòng tự động)"),
            f"- **Block Flow (ảnh):** {st.get('image_style_block', '')}",
            f"- **Block Flow (chuyển động):** {st.get('video_motion_block', '')}"] if st.get("atlas") else []),
         f"- **Hợp chủ đề (tags):** {', '.join(st.get('tags') or []) or '—'}",
         f"- **Nền đen tối thiểu:** {int(float(st.get('black_min', 0)) * 100)}% khung hình (QA đo)", ""]
    if st.get("not"):
        L += ["## Nó KHÔNG phải là", ""] + [f"- {x}" for x in st["not"]] + [""]
    if pal:
        L += ["## Bảng màu (nền đen + tối đa 2–3 màu)", ""] + [f"- `{k}` {v}" for k, v in pal.items() if not k.startswith("_")]
        L += ([f"- {pal['_doc']}"] if pal.get("_doc") else []) + [""]
    L += ["## Chữ (text_fx / thumbnail)", "",
          f"- font `{st['font']}` · cỡ {st['size']} · {'IN HOA' if st.get('uppercase') else 'chữ thường'}"
          f" · vào bằng `{st.get('intro')}` ({st.get('intro_frames')} frame) · số `{st.get('number_fill')}`", ""]
    if pc:
        L += ["## Luật nhịp", ""] + [f"- **{k}:** {'có' if v is True else 'không' if v is False else v}" for k, v in pc.items()] + [""]
    if mk:
        L += ["## Dấu (mũi tên / vòng / nhãn)", ""] + [f"- **{k}:** {v}" for k, v in mk.items()] + [""]
    L += ["## Chuyển cảnh · âm thanh · giọng · thumbnail", "", f"- chuyển cảnh: {', '.join(st.get('transitions') or []) or '—'}",
          f"- gói SFX (cue chung → âm): {', '.join(f'{k}→{v}' for k, v in (st.get('sfx_pack') or {}).items()) or '—'}",
          f"- nhạc: {mu.get('mood', '—')}" + (f" · {mu['bpm']} BPM" if mu.get("bpm") else ""),
          f"- persona giọng: {st.get('voice_persona', '—')}", f"- thumbnail: {st.get('thumbnail', '—')}", ""]
    if fl:
        L += ["## Cho Flow (khi style này dùng clip Flow)", "", f"- image_style: {fl.get('medium', '')} — {fl.get('look', '')}",
              f"- video_motion: {fl.get('motion', '—')}", ""]
    if src:
        L += ["## Nguồn", "", f"- {src.get('repo')} — {src.get('url')} @ `{src.get('sha')}` · license: {src.get('license')}",
              f"- lấy từ: {src.get('from')}", f"- cách chuyển: {src.get('how')}", ""]
    return "\n".join(L)


def write_cards(names=None):
    out = []
    for name in names or available():
        if not textstyle.load_style(name).get("not"):   # chỉ style có đủ thẻ (vòng 7 trở đi)
            continue
        p = os.path.join(textstyle.STYLES_DIR, f"{name}.md")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(card_md(name))
        out.append(p)
    return out
