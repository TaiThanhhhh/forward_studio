"""Engine `html` — motion graphics Canvas 2D trên nền đen (mã vẽ: core.js, looks.js, beats.js, icons.js).

Danh sách beat/look ở đây phải khớp với mã JS (tests/test_engines.py đối chiếu). Schema tham số từng beat: PARAMS —
dùng để validate storyboard và để brief LLM biết viết gì; không có nội dung video nào trong mã engine.
"""

import functools
import os
import re

BEATS = ("title", "drop", "counter", "compare", "graph", "process", "scale", "callout", "fact", "scene", "outro",
         "units", "timeline", "split", "meter")
LOOKS = ("flat", "boil", "iso", "hud", "synth", "sticker", "swiss", "spy", "picto", "zoom", "flow", "sketch", "gallery",
         "halftone", "comic", "pixel16", "sprite8", "silhouette", "cutout", "lineart", "vox", "story")

# beat → (trường bắt buộc, mô tả một dòng cho brief). Mọi beat nhận thêm: kicker, title, hit (0..1).
PARAMS = {
    "title": ((), "kicker, title, sub, icon, icon_role — thẻ mở đầu/hook"),
    "drop": (("a", "b"), "a{icon,label,role}, b{icon,label,p}, result, hit, sfx — A rơi/đi vào B rồi có kết quả"),
    "counter": (("to",), "from, to, unit, label, decimals, prefix, suffix, icon, land (+ per, per_label for layout units; "
                         "min, max, danger for layout gauge) — số chạy tới giá trị"),
    "compare": (("left", "right"), "left/right{icon,label,value,unit}, vs, result (+ faster higher|lower for race, per for "
                                   "units/stack, by linear|area for overlay) — hai cột so sánh đúng tỉ lệ"),
    "graph": (("points",), "points[[x,y]…], x_label, y_label, y_unit, marks[{x,label}], decimals — đường cong vẽ dần"),
    "process": (("steps",), "steps[{icon,label}] (≤4; loop/domino ≤6, nest ≤5) (+ cycles, center for loop; ratio for "
                            "nest) — chuỗi bước có số, đọc từ trên xuống"),
    "scale": (("items",), "items[{label,size,unit,icon,role}] — thang kích thước, camera zoom theo thang log"),
    "callout": (("icon",), "icon, icon_role, labels[{text,side,y}] (≤4) — một vật + nhãn có đường dẫn"),
    "fact": (("text",), "kicker, text, em, icon (+ front for layout flip, by for layout quote) — câu chốt/twist, `em` là "
                        "cụm nhấn"),
    "scene": (
        ("actors",),
        "kicker, title, actors[{id, icon | lottie | rive (user assets), x, y (0..1 of the frame), size (px), role, rot, "
        "in, out (u 0..1), "
        "keys[{u, x, y, size, rot, p, alpha, ease}]}], labels[{text, x, y | of (actor id), u, tag}], arrows[{from, to, u}], "
        "fx[{kind: burst|shockwave|smoke|splash|sparkle, x, y | at (actor id), u}] — FREE STAGING: several props/characters "
        "moving and interacting (use it for the story's key moments, not only one centred icon). DEPTH: actor/key `z` "
        "(0 = in focus, 1–4 = far: smaller, parallax, depth-of-field blur, fades into the dark; -0.5 = right at the lens), "
        "camera[{u, x, y, z (dolly in), rot (roll °), focus (z in focus → rack focus)}], "
        "depth false|{dof, fog, layers, fg}; "
        "MOTION VERBS: key {u, verb, dur, args} or actor `verb` + `args` (e.g. heartbeat{bpm}, shake, squash, float, spin)",
    ),
    "units": (
        ("groups",),
        "groups[{label, value, icon, role}] (1–3), per (real units per icon; auto = exact count ≤ 120, else 10/50/100…), "
        "per_label, unit, land, result — ISOTYPE: one icon per real unit, grouped in tens (people, bottles, games…)",
    ),
    "timeline": (
        ("events",),
        "events[{t (year or number), label, icon, role, t_label}] (2–8), unit, format year|number, scale linear|log — "
        "real time gaps set the spacing; the camera travels along the events through parallax layers",
    ),
    "split": (
        ("a", "b"),
        "a/b{label, icon, action pulse|spin|run|fill|bounce|drip|count|grow, rate (per minute: bpm, rpm, drops/min…), "
        "value, unit, role} — SPLIT SCREEN: two actions on ONE shared clock at their real rates (a 72 vs 157 BPM heart)",
    ),
    "meter": (
        ("kind",),
        "kind ecg|battery|tank|thermo|dial, value (ecg: bpm), from (start value → ramps to value), min, max, unit, label, "
        "danger, decimals, land, sweep (ecg seconds per screen) — a physical meter whose motion IS the data (ECG beats "
        "at the real bpm, battery %, tank level, mercury, needle)",
    ),
    "outro": ((), "teaser, follow, next_prefix — thẻ kết + vòng lặp"),
}


# Biến thể bố cục của từng beat (beats.js). Không ghi `layout` → tool tự chọn, xoay vòng theo video và theo shot để hai
# video (và hai shot cùng beat trong một video) không cùng một bố cục. Phần tử đầu = bố cục gốc.
LAYOUTS = {
    "title": ("center", "left", "hero", "kinetic", "reveal"),
    "counter": ("ring", "giant", "bar", "odometer", "flap", "units", "gauge"),
    "compare": ("bars", "split", "balance", "race", "units", "stack", "overlay"),
    "fact": ("center", "stamp", "left", "flip", "quote"),
    "process": ("list", "path", "loop", "nest", "domino"),
}

# Một dòng cho brief: bố cục nào hợp với loại dữ liệu nào (tiếng Anh — LLM đọc).
LAYOUT_HELP = {
    "title": {"center": "icon on a ground under the title",
              "left": "big left-aligned title, giant prop bleeding off the edge",
              "hero": "prop fills the frame, title slammed over it",
              "kinetic": "word-by-word kinetic type, `em` word highlighted",
              "reveal": "iris opens on the prop, then rack focus pulls the title sharp (depth)"},
    "counter": {"ring": "number inside a filling ring", "giant": "one huge number + progress bar",
                "bar": "column rises like a water level", "odometer": "mechanical digit wheels roll (distances, totals)",
                "flap": "split-flap board flips digit by digit (scores, prices, times)",
                "units": "isotype: the real count of icons drops into a grid (people, items; `per` for big numbers)",
                "gauge": "needle dial with a red zone (`danger`), overshoots and jitters like a live sensor"},
    "compare": {"bars": "two bars to scale", "split": "split frame, two giant props face off",
                "balance": "balance scale tips to the heavier side",
                "race": "two actors run toward the camera; speed ∝ value (`faster: lower` for times)",
                "units": "two isotype piles fill at the same rate — the bigger keeps going",
                "stack": "objects stack into two towers, height ∝ value",
                "overlay": "the smaller shape slides inside the bigger one, true-scale ratio ×N"},
    "fact": {"center": "centred statement", "stamp": "key phrase stamped on", "left": "typed left-aligned with a margin bar",
             "flip": "card flips from `front` (myth/question) to the fact",
             "quote": "big quote marks, typed quote, `by` source"},
    "process": {"list": "numbered steps top to bottom", "path": "steps on a curved path, a dot travels along",
                "loop": "steps on a cycle, a token laps `cycles` times (feedback loops)",
                "nest": "zoom from macro into micro, each step inside the previous one (body → cell → molecule)",
                "domino": "each step is a domino that knocks over the next (cause → effect chains)"},
}


def _n(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def layout_fits(scene, layout, params):
    """Dữ liệu có hợp bố cục không — CÙNG điều kiện với LAYOUT10 trong beats.js (không hợp → JS vẽ bố cục gốc)."""
    p = params or {}
    words = len(str(p.get("title") or "").split())
    steps = len(p.get("steps") or [])
    lv = _f((p.get("left") or {}).get("value")) if isinstance(p.get("left"), dict) else None
    rv = _f((p.get("right") or {}).get("value")) if isinstance(p.get("right"), dict) else None
    two = lv is not None and rv is not None and lv >= 0 and rv >= 0
    to = abs(_f(p.get("to", p.get("value"))) or 0.0)
    rules = {
        ("title", "kinetic"): 2 <= words <= 9, ("title", "reveal"): bool(p.get("title")),
        ("counter", "odometer"): to < 1e9, ("counter", "flap"): to < 1e9, ("counter", "units"): to > 0,
        ("compare", "race"): two and max(lv, rv) > 0, ("compare", "units"): two and max(lv, rv) > 0,
        ("compare", "stack"): two and max(lv, rv) > 0, ("compare", "overlay"): two and min(lv, rv) > 0,
        ("fact", "flip"): bool(p.get("text")),
        ("fact", "quote"): bool(p.get("text")) and len(str(p.get("text"))) <= 180,
        ("process", "loop"): steps >= 3, ("process", "nest"): steps >= 2, ("process", "domino"): steps >= 2,
    }
    return rules.get((scene, layout), layout in LAYOUTS.get(scene, ()))


def pick_layout(scene, seed, used, params=None):
    """Bố cục cho một shot: xoay vòng theo hạt giống của video, tránh bố cục shot cùng beat trước đó đã dùng.
    params (tuỳ chọn): bỏ các bố cục không hợp dữ liệu của shot (vd overlay khi một bên = 0)."""
    import hashlib  # noqa: PLC0415
    opts = LAYOUTS.get(scene)
    if not opts:
        return None
    if params is not None:
        opts = tuple(o for o in opts if layout_fits(scene, o, params)) or opts[:1]
    h = int(hashlib.sha1(f"{seed}:{scene}".encode()).hexdigest()[:8], 16)
    prev = used.get(scene, [])
    k = len(prev)
    order = [opts[(h + k + j) % len(opts)] for j in range(len(opts))]
    pick = next((o for o in order if o not in prev), None) or next((o for o in order if not prev or o != prev[-1]), order[0])
    used.setdefault(scene, []).append(pick)
    return pick


PART_KINDS = ("circle", "rect", "poly", "line", "arc")


def _read(name):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name), encoding="utf-8") as fh:
        return fh.read()


def _names(src, marker):
    body = src[src.index(marker) : src.index("\n};", src.index(marker))]
    return set(re.findall(r"^  (\w+): ", body, flags=re.M))


def _aliases(src):
    out = []
    for keys, ic in re.findall(r"\[\[([^\]]*)\], '(\w+)'\]", src):
        out += [(k, ic) for k in re.findall(r"'([^']+)'", keys)]
    return out


@functools.cache
def icon_table():
    """(tên icon, [(từ khoá, icon)]) đọc thẳng từ icons.js + icons_channel.js — một nguồn sự thật cho JS và Python.
    Thứ tự từ khoá giống JS: icons.js trước, icons_channel.js sau (sort theo độ dài là ổn định)."""
    core, chan = _read("icons.js"), _read("icons_channel.js")
    names = _names(core, "export const ICONS = {") | _names(chan, "export const CHANNEL_ICONS = {")
    return names, _aliases(core[: core.index("export function iconFor")]) + _aliases(chan)


@functools.cache
def icon_groups():
    """{nhóm: [icon]} — đọc GROUPS trong icons_channel.js (để brief liệt kê đạo cụ theo mảng chủ đề của kênh)."""
    src = _read("icons_channel.js")
    body = src[src.index("export const GROUPS = {") :]
    body = body[: body.index("\n};")]
    return {g: re.findall(r"'([^']+)'", items) for g, items in re.findall(r"'([^']+)': \[([^\]]*)\]", body)}


def icon_for(name):
    """Giống iconFor() của icons.js: tên icon → icon; cụm từ → từ khoá đầu tiên khớp; không khớp → None (JS vẽ 'dot')."""
    names, aliases = icon_table()
    s = str(name or "").lower().strip()
    if s in names:
        return s
    padded = f" {s} "
    flat = sorted(aliases, key=lambda a: -len(a[0]))   # cụm dài trước — giống FLAT trong icons.js (sort ổn định)
    for k, ic in flat:
        if f" {k} " in padded or f" {k}s " in padded:
            return ic
    for k, ic in flat:
        if len(k) >= 4 and k in s:   # chuỗi con: chỉ từ khoá ≥ 4 ký tự (giống icons.js)
            return ic
    return None


def _icons_in(params):
    """Mọi giá trị khoá 'icon' trong params (lồng nhau: a/b, left/right, steps[], items[])."""
    out = []
    if isinstance(params, dict):
        for k, v in params.items():
            if k == "icon" and v not in (None, ""):
                out.append(v)
            else:
                out += _icons_in(v)
    elif isinstance(params, list):
        for v in params:
            out += _icons_in(v)
    return out


@functools.cache
def _js_list(fname, const):
    """Mảng hằng `const NAME = ['a', 'b']` trong mã JS của engine — từ vựng một nguồn (JS vẽ, Python kiểm)."""
    m = re.search(rf"const {const} = \[([^\]]*)\]", _read(fname))
    return tuple(re.findall(r"'(\w+)'", m.group(1))) if m else ()


def split_actions():
    return _js_list("beats.js", "SPLIT_ACTS")


def meter_kinds():
    return _js_list("beats.js", "METER_KINDS")


@functools.cache
def rig_vocab():
    """Nhân vật 2D `rig:<loài>` của rig2d.js (WP-H1): {species, aliases, tokens} — None nếu engine chưa có rig2d.js."""
    try:
        src = _read("rig2d.js")
    except OSError:
        return None
    sp = re.search(r"export const SPECIES = \{(.*?)\n\};", src, re.S)
    al = re.search(r"export const RIG_ALIASES = \{([^}]*)\}", src)
    toks = {"actions": _js_list("rig2d.js", "ACTIONS"), "exprs": _js_list("rig2d.js", "EXPRS"),
            "faces": _js_list("rig2d.js", "FACES") or ("left", "right"), "hairs": _js_list("rig2d.js", "HAIRS")}
    return {"species": tuple(re.findall(r"^  (\w+): \{", sp.group(1), re.M)) if sp else (),
            "aliases": dict(re.findall(r"(\w+): '(\w+)'", al.group(1))) if al else {}, **toks}


def check_rig(name):
    """"rig:dog:walk:happy" → lỗi (tiếng Việt) hoặc None. Giống parseRig() của rig2d.js."""
    v = rig_vocab()
    if v is None:
        return f"icon '{name}': engine chưa có nhân vật 2D (engines/html/rig2d.js) — dùng icon thường."
    raw, *rest = [t.strip() for t in str(name)[4:].lower().split(":") if t.strip()] or [""]
    if raw not in v["species"] and raw not in v["aliases"]:
        return f"icon '{name}': loài '{raw}' không có (có: {', '.join(v['species'])}; bí danh: {', '.join(v['aliases'])})."
    ok = set(v["actions"]) | set(v["exprs"]) | set(v["faces"]) | set(v["hairs"])
    bad = [t for t in rest if t not in ok]
    return (f"icon '{name}': '{', '.join(bad)}' không phải hành động ({'|'.join(v['actions'])}) hay biểu cảm "
            f"({'|'.join(v['exprs'])}) hay hướng (left|right).") if bad else None


def check_icon(icon):
    if isinstance(icon, str) and icon.strip().lower().startswith("rig:"):
        return check_rig(icon.strip())
    if isinstance(icon, dict):
        parts = icon.get("parts")
        if not isinstance(parts, list) or not parts:
            return 'icon tự ghép cần {"parts": [{"k": "circle", "x": 0, "y": 0, "r": 0.6, "role": "hot"}, …]}'
        bad = [p for p in parts if not isinstance(p, dict) or p.get("k") not in PART_KINDS]
        return f"icon parts: 'k' phải là {'|'.join(PART_KINDS)}" if bad else None
    if isinstance(icon, str) and icon.startswith("svg:"):
        return None                                   # SVG nhập: userassets.errors kiểm tên có trên đĩa
    if icon_for(icon) is None:
        names = sorted(icon_table()[0])
        return (
            f"icon '{icon}' không có trong thư viện (sẽ thành chấm tròn). Dùng một tên gần nghĩa: {', '.join(names)} "
            '— hoặc tự ghép {"parts": [...]} từ circle/rect/poly/line/arc (toạ độ -1..1, role hot|cold|accent|ink|dim).'
        )
    return None


def validate(scene, params):
    """Lỗi (tiếng Việt) của một shot html: beat có tồn tại, đủ trường bắt buộc, icon vẽ được."""
    if scene not in BEATS:
        return [f"beat html '{scene}' không có (có: {', '.join(BEATS)})."]
    need = PARAMS[scene][0]
    miss = [k for k in need if (params or {}).get(k) in (None, "", [], {})]
    errs = [f"beat html '{scene}' thiếu params: {', '.join(miss)} ({PARAMS[scene][1]})."] if miss else []
    lay = (params or {}).get("layout")
    if lay and lay not in LAYOUTS.get(scene, ()):
        errs.append(f"beat html '{scene}': layout '{lay}' không có (có: {', '.join(LAYOUTS.get(scene, ())) or '—'}).")
    if lay and lay in LAYOUTS.get(scene, ()) and not layout_fits(scene, lay, params):
        errs.append(f"beat html '{scene}': dữ liệu không hợp layout '{lay}' ({LAYOUT_HELP[scene].get(lay, '')}) — "
                    f"engine sẽ vẽ bố cục gốc '{LAYOUTS[scene][0]}'. Sửa dữ liệu hoặc bỏ `layout`.")
    errs += [f"beat html '{scene}': {e}" for e in _beat_errors(scene, params or {})]
    errs += [e for e in (check_icon(i) for i in _icons_in(params)) if e]
    from vidlib import userassets  # noqa: PLC0415 — "svg:<tên>", actor lottie/rive phải có trong assets/user/

    errs += [f"beat html '{scene}': {e}" for e in userassets.errors(params)]
    return errs


def _nice(x):
    """Giống nice() của beats.js: bội số đẹp ≥ x (1 · 2 · 2.5 · 5 × 10^k)."""
    import math  # noqa: PLC0415
    if not x > 0:
        return 1
    p = 10 ** math.floor(math.log10(x))
    return next((float(f"{m * p:.6g}") for m in (1, 2, 2.5, 5, 10) if m * p >= x * 0.9999), 10 * p)


def per_unit(vals, cap=100, given=0):
    """Giống perUnit() của beats.js: mỗi biểu tượng isotype = bao nhiêu đơn vị thật."""
    if given and given > 0:
        return given
    vmax = max([abs(v) for v in vals] + [1e-9])
    if vmax > cap:
        return _nice(vmax / cap)
    return 1 if all(float(v).is_integer() for v in vals) or vmax >= 8 else _nice(vmax / 16)


MAX_UNITS = 400   # biểu tượng isotype tối đa một shot (đọc được + render nhanh)
SPLIT_RATE = {"pulse", "spin", "bounce", "drip", "count"}


def _verb_errors(items, where):
    """Kiểm verb bằng lib/motion (WP-M) nếu có; bản cũ chưa có verb → bỏ qua (engine dùng bộ dự phòng)."""
    try:
        from lib import motion  # noqa: PLC0415
    except ImportError:
        return []
    fn = getattr(motion, "verb_errors", None)
    return fn(items, where) if callable(fn) and items else []


def _scene_errors(p):
    errs, rv = [], rig_vocab()
    acts = p.get("actors") or []
    for i, a in enumerate(acts if isinstance(acts, list) else []):
        if not isinstance(a, dict):
            continue
        tag = f"actor '{a.get('id') or i}'"
        for k in [a, *[k for k in a.get("keys") or [] if isinstance(k, dict)]]:
            z = k.get("z")
            if z is not None and not (_n(z) and -0.85 <= z <= 20):
                errs.append(f"{tag}: z = {z!r} — chiều sâu là số -0.85..20 (0 = mặt phẳng nét, 1–4 = xa, "
                            "-0.5 = sát ống kính).")
            for key in ("action", "expr"):
                v = k.get(key)
                pool = (rv or {}).get(key + "s" if key == "action" else "exprs") or ()
                if v is not None and rv is not None and v not in pool:
                    errs.append(f"{tag}: {key} '{v}' không có (có: {'|'.join(pool)}).")
        items = list(a.get("do") or []) + [k for k in a.get("keys") or [] if isinstance(k, dict) and k.get("verb")]
        if a.get("verb"):
            items.append({"verb": a["verb"], "args": a.get("args") or {}})
        errs += _verb_errors(items, tag)
    cam = p.get("camera")
    if cam is not None:
        if not isinstance(cam, list) or not all(isinstance(k, dict) for k in cam):
            errs.append("camera là danh sách key [{u, x, y, z, rot, focus}].")
        else:
            for k in cam:
                if not (_n(k.get("u", 0)) and 0 <= k.get("u", 0) <= 1):
                    errs.append("camera[].u trong 0..1.")
                bad = [f for f in ("x", "y", "z", "rot", "focus") if f in k and not _n(k[f])]
                if bad:
                    errs.append(f"camera[]: {', '.join(bad)} phải là số.")
                if _n(k.get("z")) and not -3 <= k["z"] <= 0.8:
                    errs.append("camera[].z (dolly) trong -3..0.8 (dương = tiến vào; ≥ 0.85 là xuyên qua mặt phẳng nét).")
    d = p.get("depth")
    if d is not None and not isinstance(d, (bool, dict)):
        errs.append("depth là true/false hoặc {dof, fog, layers, fg}.")
    if isinstance(d, dict):
        bad = [k for k in d if k not in ("dof", "fog", "layers", "fg")]
        if bad:
            errs.append(f"depth: khoá lạ {', '.join(bad)} (có: dof, fog, layers, fg).")
        errs += [f"depth.{k} là số ≥ 0." for k in ("dof", "fog") if k in d and not (_n(d[k]) and d[k] >= 0)]
    return errs


def _beat_errors(scene, p):  # noqa: C901 — một nhánh mỗi beat
    """Lỗi dữ liệu riêng của beat/bố cục vòng 10 (beat cũ: không đổi)."""
    errs = []
    if scene == "scene":
        return _scene_errors(p)
    if scene == "counter" and p.get("layout") == "units":
        to = _f(p.get("to", p.get("value"))) or 0
        n = abs(to) / per_unit([to], _f(p.get("max_units")) or 100, _f(p.get("per")) or 0)
        if n > MAX_UNITS:
            errs.append(f"layout units: {n:.0f} biểu tượng (> {MAX_UNITS}) — tăng `per`.")
    if scene == "units":
        gs = p.get("groups")
        if not isinstance(gs, list) or not 1 <= len(gs) <= 3 or not all(isinstance(g, dict) for g in gs):
            return ["groups là 1–3 nhóm {label, value, icon}."]
        vals = [_f(g.get("value")) for g in gs]
        if any(v is None or v < 0 for v in vals):
            return ["groups[].value là số ≥ 0 (số đơn vị thật)."]
        per = per_unit(vals, _f(p.get("max_units")) or 120, _f(p.get("per")) or 0)
        if max(vals) / per > MAX_UNITS:
            errs.append(f"units: {max(vals) / per:.0f} biểu tượng một nhóm (> {MAX_UNITS}) — tăng `per`.")
    if scene == "timeline":
        ev = p.get("events")
        if not isinstance(ev, list) or not 2 <= len(ev) <= 8 or not all(isinstance(e, dict) for e in ev):
            return ["events là 2–8 mốc {t, label, icon}."]
        if any(_f(e.get("t")) is None for e in ev):
            errs.append("events[].t là số (năm hoặc giá trị thời gian) — chữ hiển thị riêng đặt ở t_label.")
        if any(not str(e.get("label") or "").strip() for e in ev):
            errs.append("events[].label bắt buộc (tiếng Anh ngắn).")
        if p.get("scale") not in (None, "linear", "log"):
            errs.append("timeline.scale là linear | log.")
        if p.get("scale") == "log" and any((_f(e.get("t")) or 0) <= 0 for e in ev):
            errs.append("timeline.scale log cần mọi t > 0.")
        if p.get("format") not in (None, "year", "number"):
            errs.append("timeline.format là year | number.")
    if scene == "split":
        acts = split_actions()
        for side in ("a", "b"):
            o = p.get(side)
            if not isinstance(o, dict):
                continue
            a = o.get("action")
            if a is not None and a not in acts:
                errs.append(f"split.{side}.action '{a}' không có (có: {'|'.join(acts)}).")
                continue
            a = a or ("pulse" if o.get("rate") else "grow")
            r = _f(o.get("rate"))
            if a in SPLIT_RATE and not (r is not None and 1 <= r <= 600):
                errs.append(f"split.{side}: action '{a}' cần rate (số lần/phút thật, 1..600 — vd nhịp tim 72).")
            if a not in SPLIT_RATE and _f(o.get("value")) is None:
                errs.append(f"split.{side}: action '{a}' cần value (số) — quãng/mức/cỡ tỉ lệ theo value.")
    if scene == "meter":
        kinds = meter_kinds()
        if p.get("kind") not in kinds:
            return [f"meter.kind '{p.get('kind')}' không có (có: {'|'.join(kinds)})."]
        v = _f(p.get("value", p.get("bpm", p.get("to"))))
        if v is None:
            return ["meter cần value (số; ecg: nhịp/phút)."]
        if p["kind"] == "ecg" and not all(20 <= x <= 300 for x in (v, _f(p.get("from", v)) or v)):
            errs.append("meter ecg: value/from là nhịp tim 20..300 BPM.")
        lo, hi = _f(p.get("min")), _f(p.get("max"))
        if lo is not None and hi is not None and lo >= hi:
            errs.append("meter: min phải < max.")
    return errs


def workers():
    """Số trình duyệt song song. Đo (docs/PERF.md mục 3): 2 nhanh nhất cho shot 2–5 s; nhiều hơn tốn thời gian khởi động."""
    from vidlib.common import channel  # noqa: PLC0415

    w = int(channel().get("code_render", {}).get("html_workers") or 0)
    return w or 2
