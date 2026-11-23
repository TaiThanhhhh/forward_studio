"""Đường dựng "code-animated shot" (mode: code) — cầu nối storyboard ↔ engine three.js (engines/three/).

Shot code khai báo:  "mode": "code", "code": {"scene": "<engines/three/scenes/*.js>", "params": {...}}
Ý tưởng mới dùng cảnh tổng quát `stage` (đạo cụ + keyframe bằng dữ liệu, schema ở đầu engines/three/scenes/stage.js);
các cảnh khác là preset có tham số.
- job.json: cảnh + params + số frame (theo timeline) + palette/ink/font của STYLE video → cùng palette, cùng độ dày
  nét với shot Flow cạnh nó (styles/<style>.json → world, cast_palette).
- Frame render ở work/code/<sid>/fNNNN.jpg (coderender: song song + RESUME).
- export_frame(): xuất một frame của shot code làm ảnh Start/End cho shot Flow nối liền (hai đường dựng tham chiếu
  lẫn nhau).
"""
import contextlib
import os

from engines import adapter

from . import coderender, textstyle  # noqa: F401 — coderender: nơi khác gọi codeshot.coderender.job_hash
from .common import FPS, H, ROOT, W, StudioError, load_json

SCENES_DIR = os.path.join(ROOT, "engines", "three", "scenes")

# Từ khoá → cảnh code nên dùng (storyboard tự chọn mode code cho cảnh Flow làm kém)
AUTO_SCENES = [
    (("balance scale", "weighing scale", "scale pan", "on a scale", " scale "), "scale"),
    (("thermometer", "temperature reading", "°c reading"), "thermometer"),
    (("pressure gauge", "dial gauge", "gauge"), "gauge"),
    (("vacuum chamber", "bell jar"), "vacuum"),
    (("next experiment", "outro", "loop back"), "outro"),
]
WEAK_FOR_FLOW = ("diagram", "cross-section", "cross section", "cutaway", "to scale", "size comparison", "ruler",
                 "measuring", "gauge", "thermometer", "counter", "readout", "scale", "label", "sign that says",
                 "written", "text on", "chart", "graph")


def engine_rev(scene=None, engine=None):
    """Hash mã engine (engine=None: gộp cả ba engine xuất frame — dùng cho dấu vân tay render) + file cảnh `scene`
    — đưa vào job để RESUME không dùng lại frame của engine cũ, mà thêm/sửa cảnh KHÁC không làm render lại."""
    if engine:
        return adapter.get(engine).rev(scene)
    return "-".join(adapter.get(e).rev(scene if e == "three" else None) for e in adapter.FRAME_ENGINES)


def scenes(engine="three"):
    return adapter.get(engine).scenes()


def _looks_html(scene, params):
    """Cảnh trùng tên ở three.js và html (scale, outro): params có trường bắt buộc của beat html mà cảnh three.js
    không khai trong dòng `// params:` → shot này viết cho html (video trộn nhiều engine, style code_engine = three)."""
    from engines import html  # noqa: PLC0415
    need = [k for k in html.PARAMS.get(scene, ((),))[0] if params.get(k) not in (None, "", [], {})]
    if not need:
        return False
    three_keys = adapter.three_param_names(scene)
    return any(k not in three_keys for k in need)


def engine_of(shot, style=None):
    """Engine dựng một shot code: `code.engine` tường minh → engine đó; không ghi → three nếu cảnh có trong
    engines/three/scenes, ngược lại engine của style (`code_engine` trong styles/<style>.json); beat mà engine đó không
    có → html. Cảnh trùng tên ở three và html (scale, outro) → theo params (xem _looks_html)."""
    c = shot.get("code") or {}
    e = c.get("engine")
    if e in adapter.ENGINE_NAMES:
        return e
    sc = c.get("scene")
    if not sc:
        return None
    pref = None
    if style and style != "auto":
        with contextlib.suppress(Exception):
            pref = textstyle.load_style(style).get("code_engine")
    if pref in ("html", "manim"):                     # style dựng bằng engine mới: beat trùng tên (outro, scale) thuộc về nó
        for cand in (pref, "html"):
            if sc in scenes(cand):
                return cand
    if sc in scenes("three"):
        if sc in scenes("html") and _looks_html(sc, c.get("params") or {}):
            return "html"                             # video trộn engine: `scale` kiểu thang kích thước (items) là html
        return "three"
    for cand in ("html", "manim"):
        if sc in scenes(cand):
            return cand
    return "three"


def is_3d(shot):
    """Shot code xuất frame riêng (three.js, html hoặc manim) → work/code/<sid>/frames. (Tên giữ từ vòng 5.)"""
    c = shot.get("code") or {}
    return bool(c.get("scene")) and c.get("engine") != "board"


def is_board(shot):
    """Shot dựng bằng engine board (engines/board/, Python) — engine thứ hai của mode: code."""
    return (shot.get("code") or {}).get("engine") == "board" and not is_3d(shot)


def board_frames_dir(proj, sid):
    return os.path.join(proj, "work", "board", "frames", sid)


def have_all_dir(d, n):
    return all(os.path.exists(os.path.join(d, f"f{f:04d}.jpg")) for f in range(n))


def suggest(shot):
    """(scene hoặc None, lý do) — cảnh mà Flow hay làm kém: sơ đồ, cân/thước/nhiệt kế/bộ đếm, chữ trong cảnh."""
    txt = " ".join([shot.get("subject", ""), shot.get("start_frame", {}).get("desc", ""),
                    " ".join(a.get("do", "") if isinstance(a, dict) else str(a) for a in shot.get("action") or [])]).lower()
    txt = f" {txt} "
    for keys, scene in AUTO_SCENES:
        if any(k in txt for k in keys) and scene in scenes():
            return scene, f"'{next(k for k in keys if k in txt).strip()}' → cảnh code '{scene}'"
    hit = next((k for k in WEAK_FOR_FLOW if k in txt), None)
    return None, (f"'{hit}' — Flow hay làm kém loại cảnh này: dùng mode code, cảnh 'stage' (ghép đạo cụ bằng dữ liệu)"
                  if hit else "")


def world(style):
    st = textstyle.load_style(style)
    base = textstyle.load_style("forward")
    if st.get("world"):
        return st["world"], st.get("cast_palette") or base.get("cast_palette") or {}
    import copy  # noqa: PLC0415
    w = copy.deepcopy(base.get("world") or {})
    cp = copy.deepcopy(base.get("cast_palette") or {})
    html_cfg = st.get("html") or {}
    pal = html_cfg.get("palette") or st.get("palette") or {}
    look = html_cfg.get("look", "flat")
    def_roles = {"zoom": {"hot": "c", "cold": "b", "accent": "a"},
                 "flow": {"hot": "b", "cold": "ink", "accent": "a"}}.get(
        look, {"hot": "a", "cold": "b", "accent": "a" if look in ("hud", "boil", "sticker", "swiss", "picto") else "c"}
    )
    roles = {**def_roles, **(html_cfg.get("roles") or {})}
    ink = pal.get("ink") or "#FFFFFF"
    acc = pal.get(roles["accent"]) or pal.get("a") or "#1849F7"
    hot = pal.get(roles["hot"]) or pal.get("a") or "#FF3B30"
    cold = pal.get(roles["cold"]) or pal.get("b") or acc
    c = w.setdefault("colors", {})
    c.update({"white": ink, "chalk": ink, "label": ink, "dial": ink, "accent": acc, "accent_glow": acc,
              "danger": hot, "water": cold})
    c.setdefault("orange", "#FF9A3D")
    w.setdefault("ink", {}).update({"color": "#000000", "rim": ink})
    w.setdefault("lights", {})["rim"] = 2.0
    cp.update({"body": ink, "accent": acc, "rim": ink})
    return w, st.get("cast_palette") or cp


def font_entry(style):
    st = textstyle.load_style(style)
    return {"family": "StyleFont", "url": "/assets/fonts/" + st["font"]}


def code_dir(proj, sid):
    return os.path.join(proj, "work", "code", sid)


def spec_for(proj, sb, shot, n_frames, style, spine=None):
    """Shot trong storyboard → ShotSpec của adapter chung (engines/adapter.py)."""
    if not is_3d(shot):
        raise StudioError(f"{shot['id']}: shot code cần 'code': {{'scene': …}} (có: {', '.join(scenes())}).")
    eng = engine_of(shot, style)
    scene = shot["code"]["scene"]
    if scene not in scenes(eng):
        raise StudioError(f"{shot['id']}: engine {eng} không có cảnh/beat '{scene}' (có: {', '.join(scenes(eng))}).")
    ids = [s["id"] for s in (sb or {}).get("shots", [])]
    index = [ids.index(shot["id"]) + 1, len(ids)] if shot["id"] in ids else None
    return adapter.ShotSpec(sid=shot["id"], engine=eng, scene=scene, params=shot["code"].get("params") or {},
                            frames=int(n_frames), fps=FPS, width=W, height=H, style=style,
                            work=code_dir(proj, shot["id"]), beat=shot.get("beat"), index=index, spine=spine)


def job_for(proj, sb, shot, n_frames, style, spine=None):
    """Ghi work/code/<sid>/job.json (engine three | html | manim). Trả về đường dẫn. spine: xem vidlib/spine.py."""
    eng = engine_of(shot, style) if is_3d(shot) else None
    if eng == "manim" and spine:     # Manim chỉ cần vị trí ô hàng xóm để bay camera (nội dung hàng xóm không đổi hash)
        spine = {k: v for k, v in spine.items() if k not in ("prev", "next")} | {
            side: {"n": spine[side]["n"], "tile": spine[side]["tile"]} for side in ("prev", "next") if spine.get(side)}
    spec = spec_for(proj, sb, shot, n_frames, style, spine=spine if eng in SPINE_ENGINES else None)
    return adapter.get(spec.engine).job(spec)


SPINE_ENGINES = ("html", "manim")   # engine đi được trong "một cú máy liền" (manim: hậu kỳ affine, xem spine.travel_matrix)


def assign_layouts(sb, style, extra=None, history=None):
    """Shot html chưa ghi `layout` → chọn biến thể bố cục (engines/html LAYOUTS). Vòng 10: tránh trước hết bố cục đã
    dùng TRONG video, rồi bố cục các video SINH TRƯỚC nó đã dùng (vidlib/motionplan.recent_layouts — lịch sử kênh), bỏ
    bố cục không hợp dữ liệu shot (html.layout_fits). Dự án sinh trước motion.apply_since giữ đúng cách chọn cũ.
    Ghi vào bản biên dịch (csb) — tất định nên chạy lại vẫn giống, cú máy liền thấy cùng bố cục.
    history: {beat: {layout: trọng số}} ép tay (test); None = đọc lịch sử kênh."""
    from engines import html  # noqa: PLC0415

    from . import motionplan  # noqa: PLC0415
    used = {}
    seed = sb.get("slug") or sb.get("topic", "")
    legacy = history is None and motionplan.legacy(seed)
    recent = {} if legacy else (history if history is not None else motionplan.recent_layouts(seed))
    for sh in list(sb.get("shots", [])) + [x for x in (extra or []) if x]:
        c = sh.get("code") or {}
        if not is_3d(sh) or engine_of(sh, style) != "html":
            continue
        p = c.setdefault("params", {})
        if not p.get("layout"):
            lay = (motionplan.legacy_pick_layout(c["scene"], seed, used) if legacy
                   else motionplan.pick_layout(c["scene"], seed, used, recent, p))
            if lay:
                p["layout"] = lay
        elif c["scene"] in html.LAYOUTS:
            used.setdefault(c["scene"], []).append(p["layout"])


def spine_context(sb, tl, style, extra=None):
    """{sid: spine} — các shot html (và manim) liền nhau thành một cú máy liền (vidlib/spine.py). extra: shot ngoài
    storyboard (vd OUTRO) để chuỗi nối luôn vào thẻ kết. Shot manim là "ô ma" với hàng xóm html: camera vẫn bay qua,
    html không vẽ lại nội dung Manim (khác nét) — Manim tự bay camera trên khung của nó."""
    from . import narratives, spine  # noqa: PLC0415
    shots = {s["id"]: s for s in sb.get("shots", [])}
    shots.update(extra or {})
    ids = [s["id"] for s in sb.get("shots", [])]

    def in_run(sh):
        return is_3d(sh) and engine_of(sh, style) in SPINE_ENGINES

    def entry(sh):
        if engine_of(sh, style) != "html":
            return {"scene": sh["code"]["scene"], "params": {}, "ghost": True}
        p = dict((sh.get("code") or {}).get("params") or {})
        if sh["id"] in ids and "index" not in p:
            p["index"] = [ids.index(sh["id"]) + 1, len(ids)]
        return {"scene": sh["code"]["scene"], "params": p}

    return spine.context(tl["segments"], shots, style, sb.get("slug") or sb.get("topic", ""), in_run, entry,
                         narratives.moves(sb.get("narrative_resolved")))


def _job_engine(job_path):
    return adapter.get(adapter.engine_of_job(job_path))


def meta(job_path):
    """Metadata cảnh (cue SFX, chữ trong cảnh) — engine nào cũng trả cùng dạng."""
    return _job_engine(job_path).meta(job_path)


def text_crops(job_path, frames):
    return _job_engine(job_path).text_crops(job_path, frames)


def frames_dir(proj, sid):
    return os.path.join(code_dir(proj, sid), "frames")


def have_all(proj, sid, n):
    d = frames_dir(proj, sid)
    jp = os.path.join(code_dir(proj, sid), "job.json")
    if os.path.exists(jp):
        job = load_json(jp, {})
        if job.get("engine") in ("three", "html"):
            stamp = os.path.join(d, "_job.hash")
            if not os.path.exists(stamp):
                return False
            with open(stamp, encoding="utf-8") as fh:
                if fh.read().strip() != coderender.job_hash(job):
                    return False
    return all(os.path.exists(os.path.join(d, f"f{f:04d}.jpg")) for f in range(n))


def render_shot(proj, sid, log=print, frames=None):
    job = os.path.join(code_dir(proj, sid), "job.json")
    return _job_engine(job).render(job, frames_dir(proj, sid), frames, log=log)


def render_stills(proj, sid, frames, log=print):
    """Stills cho look-check (frame lẻ) — dùng chung thư mục frames nên render đầy đủ sau đó sẽ RESUME."""
    job = os.path.join(code_dir(proj, sid), "job.json")
    return _job_engine(job).render(job, frames_dir(proj, sid), sorted(set(frames)), log=lambda m: None,
                                   workers=min(4, len(set(frames))))


def export_frame(proj, sid, f, dst):
    """Frame f của shot code → ảnh PNG (vd frames/C12_start.png cho shot Flow nối liền)."""
    from PIL import Image  # noqa: PLC0415
    src = os.path.join(frames_dir(proj, sid), f"f{f:04d}.jpg")
    if not os.path.exists(src):
        render_shot(proj, sid, frames=[f])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    Image.open(src).convert("RGB").save(dst)
    return dst


