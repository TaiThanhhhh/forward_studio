"""Engine `html` — motion graphics Canvas 2D trên nền đen (mã vẽ: core.js, looks.js, beats.js, icons.js).

Danh sách beat/look ở đây phải khớp với mã JS (tests/test_engines.py đối chiếu). Schema tham số từng beat: PARAMS —
dùng để validate storyboard và để brief LLM biết viết gì; không có nội dung video nào trong mã engine.
"""

import functools
import os
import re

BEATS = ("title", "drop", "counter", "compare", "graph", "process", "scale", "callout", "fact", "scene", "outro",
         "units", "timeline", "split", "meter", "dossier", "xray_cutaway", "hero_stat", "code_terminal", "chat_prompt")
LOOKS = ("flat", "boil", "iso", "hud", "synth", "sticker", "swiss", "spy", "picto", "zoom", "flow", "sketch", "gallery",
         "halftone", "comic", "pixel16", "sprite8", "silhouette", "cutout", "lineart", "vox", "story",
         "cosmic", "essay", "bold")
LOOK_ALIASES = {"kurzgesagt": "cosmic", "schooloflife": "essay", "infographics": "bold"}   # vòng 19 → vòng 21

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
        "heat (0..1 grounded thermal glow), in, out (u 0..1), "
        "keys[{u, x, y, size, rot, p, alpha, heat, ease}]}], "
        "labels[{text, x, y | of (actor id), u, tag, fixed}] (labels auto-dodge props/people/lenses: the engine "
        "picks the clearest spot near where you put them, once per label; fixed true = keep the exact spot), "
        "arrows[{from, to, u}], "
        "fx[{kind: burst|shockwave|smoke|splash|sparkle, x, y | at (actor id), u}] — FREE STAGING: several props/characters "
        "moving and interacting (use it for the story's key moments, not only one centred icon). DEPTH: actor/key `z` "
        "(0 = in focus, 1–4 = far: smaller, parallax, depth-of-field blur, fades into the dark; -0.5 = right at the lens), "
        "camera[{u, x, y, z (dolly in), rot (roll °), focus (z in focus → rack focus)}], "
        "depth false|{dof, fog, layers, fg}; "
        "MOTION VERBS: key {u, verb, dur, args} or actor `verb` + `args` (e.g. heartbeat{bpm}, shake, squash, float, spin). "
        "LIVING PARTS (rig characters): every reference (labels.of, arrows.from/to, fx.at, camera.at, look_at) takes "
        "\"id.part\" — part: head|eye|brain|mouth|ear|nose|neck|chest|heart|lungs|belly|stomach|hand|hand_far|foot|back|"
        "tail|wing|center|top (plain icons: center|top|bottom|left|right|screen|window|core); actor xray 0..1 (keyable: "
        "the body turns see-through) + organs [brain|heart|lungs|stomach|skeleton] (heart beats at `bpm`, lungs breathe), "
        "focus \"<part>\" (pulsing glow ring, keyable), hold \"<icon>\" (prop in the hand / in an animal's mouth), "
        "talk true|[[u0,u1]] (mouth moves), look_at \"<id>[.part]\" (eyes follow it); walk/run legs auto-sync to the "
        "distance travelled (no foot sliding). PART ZOOM: camera key {u, at: \"hero.eye\", zoom: 12} dives INTO that part "
        "(crisp vector zoom, labels fade out) — end a shot on it and start the next with transition_in \"zoom_through\". "
        "labels[].bubble speech|thought = comic bubble pointing at `of` (\"hero.mouth\" / \"hero.head\"). "
        "ROUND 23 — CAST & ANGLES: more people rig:coach|lifterf|bigguy|elder|student|office|cyclist|medic|trailrunner; "
        "actor view side|front|back (keyable: keys[{u, view}] turns the person; lifts read best front: barbell across the "
        "shoulders / in front of the thighs), outfit singlet|tank|tee|jersey|hoodie|shirt|labcoat, hair adds afro|buzz|"
        "helmet, beard stubble|full, glasses true, build 0.85..1.4; action deadlift (hip hinge, bar path vertical). "
        "ROUND 22 — REALISTIC PEOPLE: rig:athlete|marathoner|runnerf|lifter|casual|casualf (7.5-head anatomy, real "
        "running/walking gait from joint-angle curves, clothes, shoes) with actions idle|walk|run|sit|sleep|point|wave|"
        "cheer|jump|tired|curl|squat|cycle (cycle draws a real road bike); extra parts knee|thigh|calf|heel|ankle|sole|"
        "elbow|shoulder|arm|liver|spine|hip; organs also liver|spine (discs, actor `p` = compression)|muscles|vessels|"
        "fuel (glycogen stores glowing, `p` = how full). actor freeze: u (the character holds still from u — use it "
        "before zooming into a part). BACKDROP: backdrop \"city|road|gym|bedroom|track|office|studio|lab\" or "
        "{kind, floor (y of the floor line, ≈ feet y), dim} = layered NIGHT environment with parallax (never a flat "
        "black void). LENSES (magnifier inset, max 2): lenses[{of: \"id.part\", x, y, r 0.08..0.45, u, out, title, "
        "actors:[{icon, x, y (0..1 inside), size (px as on a full 1080 frame), p, keys}], flow:[{icon, count, from, to, "
        "size, speed, spread}], labels}] — a ring on the part + tangent lines + a live zoomed scene: the clearest way to "
        "show what is INSIDE (capillary in the sole, glycogen in the liver, fibers in a muscle). DETAILED PROPS: laptop, "
        "phone, chip, keyboard, server, gpu, film, reel, drawing, pencil, brain, neuron, rbc, bloodcell, macrophage and "
        "chomper (p > 0.5 = keeps chomping), fatcell, fat, glycogen, glucose, bread, pasta, vertebra, spine, disc, muscle, "
        "musclefiber, fiber (p = micro-tears), mitochondria, heart, lungs, liver, capillary (p = pinched), vesselwall, "
        "peptide, lipidchain, caffeine, adenosine, receptor (p = occupied), cup, coffeebean, bed, shoe, paper, bits, bike, "
        "denoise (p 0 = noise → 1 = clean scene)",
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
    "dossier": (
        ("headline",),
        "tag, stamp (e.g. VERIFIED|BUSTED), headline, evidence[{k, v}] (≤4), highlight (keyword swept by highlighter), "
        "visual_icon, cite — ARCHIVAL DOSSIER CARD (LEMMiNO/Johnny Harris/Fern): dark evidence file with hairline rows",
    ),
    "xray_cutaway": (
        ("core_icon",),
        "shell_icon, core_icon, flow[{from:[x,y], to:[x,y], via?:[x,y], count, role, speed}], pulse_rate (BPM), "
        "callout_num, callout_label — X-RAY CUTAWAY (Zack D. Films/Fern): blueprint shell, pulsing core & Bezier flow",
    ),
    "hero_stat": (
        ("number",),
        "number, prefix, suffix, unit, label, sub_bar{from, to, max}, bg_motif rings|bars|grid|wave, role — "
        "ARCHITECTURAL HERO STAT (Cleo Abram/Vox/Ordinary Folk): giant 180-230px number over reactive full-bleed graphics",
    ),
    "code_terminal": (
        ("lines",),
        "filename, lines[str|{text, role?, bug?}] (≤6), tokens[{text, id, role?}] (≤5), status — "
        "LITERAL CODE/TOKEN TERMINAL (Fireship/ByteByteGo): dark editor typing lines, red bug highlight & token ID chips",
    ),
    "chat_prompt": (
        ("user", "ai"),
        "user, ai, verdict, verdict_role, note — LITERAL AI CHAT PROOF: user prompt bubble, AI reply & verdict stamp",
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
    core, chan, det = _read("icons.js"), _read("icons_channel.js"), _read("icons_detail.js")
    names = (_names(core, "export const ICONS = {") | _names(chan, "export const CHANNEL_ICONS = {")
             | _names(det, "export const DETAIL_ICONS = {"))
    return names, _aliases(det) + _aliases(core[: core.index("export function iconFor")]) + _aliases(chan)


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
    """Mọi giá trị khoá icon trong params (lồng nhau: icon, visual_icon, shell_icon, core_icon)."""
    out = []
    if isinstance(params, dict):
        for k, v in params.items():
            if k in ("icon", "visual_icon", "shell_icon", "core_icon") and v not in (None, ""):
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


def hero_motifs():
    return _js_list("beats.js", "HERO_MOTIFS")


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
            "faces": _js_list("rig2d.js", "FACES") or ("left", "right"), "hairs": _js_list("rig2d.js", "HAIRS"),
            "views": _js_list("rig2d.js", "VIEWS") or ("side", "front", "back")}
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
    ok = set(v["actions"]) | set(v["exprs"]) | set(v["faces"]) | set(v["hairs"]) | set(v.get("views") or ())
    bad = [t for t in rest if t not in ok]
    return (f"icon '{name}': '{', '.join(bad)}' không phải hành động ({'|'.join(v['actions'])}) hay biểu cảm "
            f"({'|'.join(v['exprs'])}), hướng (left|right) hay góc nhìn (side|front|back).") if bad else None


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


GENERIC_PARTS = ("center", "top", "bottom", "left", "right", "screen", "window", "core")   # = GENERIC_PARTS của core.js
BUBBLES = ("speech", "thought")


def part_names():
    """Mọi tên bộ phận hợp lệ trong `"id.part"` (rig + icon thường)."""
    from . import rig2d  # noqa: PLC0415
    return tuple(dict.fromkeys((*rig2d.parts(), *GENERIC_PARTS)))


def actor_ids(p):
    """id của mọi actor của một beat `scene` (thiếu id → a0, a1… như beats.js)."""
    acts = (p or {}).get("actors") or []
    return [a.get("id") or f"a{i}" for i, a in enumerate(acts) if isinstance(a, dict)]


def ref_error(ref, ids, where):
    """Lỗi của một tham chiếu "id" | "id.part" (None nếu hợp lệ)."""
    if not isinstance(ref, str) or not ref.strip():
        return f"{where}: tham chiếu phải là chuỗi \"id\" hoặc \"id.part\"."
    aid, _, part = ref.strip().partition(".")
    if aid not in ids:
        return f"{where}: không có actor '{aid}' (có: {', '.join(ids) or '—'})."
    if part and part not in part_names():
        return f"{where}: bộ phận '{part}' không có (có: {'|'.join(part_names())})."
    return None


def _living_errors(a, tag, ids):
    """Vòng 21 — bộ phận sống của một actor: xray/organs/focus/hold/talk/look_at/bpm/slide."""
    from . import rig2d  # noqa: PLC0415
    errs, keys = [], [k for k in a.get("keys") or [] if isinstance(k, dict)]
    for k in [a, *keys]:
        if "xray" in k and not (_n(k["xray"]) and 0 <= k["xray"] <= 1):
            errs.append(f"{tag}: xray là số 0..1 (0 = thân đặc, 1 = trong suốt lộ cơ quan).")
        fp = k.get("focus")
        if fp is not None and fp is not False and fp not in part_names():
            errs.append(f"{tag}: focus '{fp}' không phải bộ phận (có: {'|'.join(part_names())}).")
    org = a.get("organs")
    if org is not None:
        lst = org if isinstance(org, list) else [org]
        bad = [o for o in lst if o not in rig2d.organs()]
        if bad:
            errs.append(f"{tag}: organs {bad} không có (có: {'|'.join(rig2d.organs())}).")
        if not any(_n(k.get("xray")) and k["xray"] > 0 for k in [a, *keys]):
            errs.append(f"{tag}: organs chỉ hiện khi xray > 0 — thêm \"xray\": 1 (hoặc key {{u, xray: 1}} để lộ dần).")
    if a.get("hold") is not None:
        e = check_icon(a["hold"])
        if e:
            errs.append(f"{tag}: hold — {e}")
    tk = a.get("talk")
    if tk is not None and tk is not True and tk is not False:
        ok = isinstance(tk, list) and all(isinstance(r, list) and len(r) == 2 and all(_n(v) and 0 <= v <= 1 for v in r)
                                          and r[0] < r[1] for r in tk)
        if not ok:
            errs.append(f"{tag}: talk là true hoặc danh sách khoảng [[u0, u1], …] (0..1, u0 < u1).")
    if a.get("look_at") is not None:
        e = ref_error(a["look_at"], ids, f"{tag}: look_at")
        if e:
            errs.append(e)
    if a.get("bpm") is not None and not (_n(a["bpm"]) and 20 <= a["bpm"] <= 240):
        errs.append(f"{tag}: bpm là số 20..240 (nhịp tim khi organs có heart).")
    return errs


def _scene_errors(p):
    errs, rv = [], rig_vocab()
    acts = p.get("actors") or []
    ids = actor_ids(p)
    for i, a in enumerate(acts if isinstance(acts, list) else []):
        if isinstance(a, dict):
            errs += _living_errors(a, f"actor '{a.get('id') or i}'", ids)
    for li, lab in enumerate(p.get("labels") or []):
        if not isinstance(lab, dict):
            continue
        if lab.get("of") is not None:
            e = ref_error(lab["of"], ids, f"labels[{li}].of")
            if e:
                errs.append(e)
        if lab.get("side") is not None and lab["side"] not in ("left", "right"):
            errs.append(f"labels[{li}].side là left|right (hướng đẩy bong bóng).")
        if lab.get("bubble") is not None:
            if lab["bubble"] not in BUBBLES:
                errs.append(f"labels[{li}].bubble là {'|'.join(BUBBLES)}.")
            elif not lab.get("of"):
                errs.append(f"labels[{li}]: bong bóng cần `of` (vd \"hero.mouth\" hoặc \"hero.head\") để đuôi chỉ "
                            "về nhân vật.")
    for ai, ar in enumerate(p.get("arrows") or []):
        if isinstance(ar, dict):
            for key in ("from", "to"):
                e = ref_error(ar.get(key), ids, f"arrows[{ai}].{key}")
                if e:
                    errs.append(e)
    for fi, fx in enumerate(p.get("fx") or []):
        if isinstance(fx, dict) and fx.get("at") is not None:
            e = ref_error(fx["at"], ids, f"fx[{fi}].at")
            if e:
                errs.append(e)
    for ci, k in enumerate(p.get("camera") or [] if isinstance(p.get("camera"), list) else []):
        if not isinstance(k, dict):
            continue
        if k.get("at") is not None:
            e = ref_error(k["at"], ids, f"camera[{ci}].at")
            if e:
                errs.append(e)
        if "zoom" in k and not (_n(k["zoom"]) and 0.5 <= k["zoom"] <= 40):
            errs.append(f"camera[{ci}].zoom là số 0.5..40 (phóng 2D về điểm nhìn; 8–20 = lao vào một bộ phận).")
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
    errs += _round22_errors(p, ids)
    return errs


@functools.cache
def backdrop_kinds():
    """Bối cảnh đêm của beat scene (đọc BACKDROPS trong backdrops.js — một nguồn sự thật)."""
    m = re.search(r"export const BACKDROPS = \[([^\]]*)\]", _read("backdrops.js"))
    return tuple(re.findall(r"'([^']+)'", m.group(1))) if m else ()


def _round22_errors(p, ids):
    """Vòng 22: backdrop (bối cảnh đêm), lenses (kính lúp), freeze (đứng hình)."""
    errs = []
    bd = p.get("backdrop")
    if bd is not None:
        kind = bd.get("kind") if isinstance(bd, dict) else bd
        if kind not in backdrop_kinds():
            errs.append(f"backdrop '{kind}' không có (có: {'|'.join(backdrop_kinds())}).")
        if isinstance(bd, dict):
            for key in ("floor", "dim", "blur"):
                if key in bd and not (_n(bd[key]) and 0 <= bd[key] <= 1.2):
                    errs.append(f"backdrop.{key} là số 0..1.2.")
    lenses = p.get("lenses")
    if lenses is not None:
        if not isinstance(lenses, list):
            errs.append("lenses là danh sách [{of, x, y, r, u, title, actors, flow, labels}].")
        else:
            for li, L in enumerate(lenses[:2]):
                if not isinstance(L, dict):
                    errs.append(f"lenses[{li}] phải là object.")
                    continue
                of = L.get("of")
                if isinstance(of, str):
                    e = ref_error(of, ids, f"lenses[{li}].of")
                    if e:
                        errs.append(e)
                elif of is not None and not (isinstance(of, list) and len(of) == 2 and all(_n(v) for v in of)):
                    errs.append(f"lenses[{li}].of là \"id.part\" hoặc [x, y].")
                if "r" in L and not (_n(L["r"]) and 0.08 <= L["r"] <= 0.45):
                    errs.append(f"lenses[{li}].r là 0.08..0.45 (phần bề rộng khung).")
                for a in (L.get("actors") or []) + (L.get("flow") or []):
                    if isinstance(a, dict) and a.get("icon") is not None:
                        e = check_icon(a["icon"])
                        if e:
                            errs.append(f"lenses[{li}]: {e}")
            if len(lenses) > 2:
                errs.append("tối đa 2 kính lúp mỗi shot (dễ đọc).")
    for i, a in enumerate(p.get("actors") or []):
        if isinstance(a, dict) and a.get("freeze") is not None and not (_n(a["freeze"]) and 0 <= a["freeze"] <= 1):
            errs.append(f"actor '{a.get('id') or i}': freeze là u 0..1 (đứng hình từ đó).")
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
    if scene == "dossier":
        ev = p.get("evidence")
        if ev is not None and (not isinstance(ev, list) or not all(isinstance(r, dict) for r in ev)):
            errs.append("dossier.evidence phải là danh sách [{k, v}].")
    if scene == "xray_cutaway":
        fl = p.get("flow")
        if fl is not None:
            if not isinstance(fl, list) or not all(isinstance(f, dict) for f in fl):
                errs.append("xray_cutaway.flow phải là danh sách [{from:[x,y], to:[x,y], via?:[x,y]}].")
            else:
                for f in fl:
                    for key in ("from", "to"):
                        pt = f.get(key)
                        if not (isinstance(pt, list) and len(pt) == 2 and all(_n(v) for v in pt)):
                            errs.append(f"xray_cutaway.flow[].{key} phải là cặp số [x, y].")
                    via = f.get("via")
                    if via is not None and not (isinstance(via, list) and len(via) == 2 and all(_n(v) for v in via)):
                        errs.append("xray_cutaway.flow[].via phải là cặp số [x, y].")
        pr = p.get("pulse_rate")
        if pr is not None and not (_n(pr) and 10 <= pr <= 300):
            errs.append("xray_cutaway.pulse_rate là nhịp BPM 10..300.")
    if scene == "hero_stat":
        motifs = hero_motifs() or ("rings", "bars", "grid", "wave")
        if p.get("bg_motif") is not None and p.get("bg_motif") not in motifs:
            errs.append(f"hero_stat.bg_motif '{p.get('bg_motif')}' không có (có: {'|'.join(motifs)}).")
        sb = p.get("sub_bar")
        if sb is not None and (not isinstance(sb, dict) or _f(sb.get("from")) is None or _f(sb.get("to")) is None):
            errs.append("hero_stat.sub_bar cần {from, to} là số.")
    return errs


def workers():
    """Số trình duyệt song song. Đo (docs/PERF.md mục 3): 2 nhanh nhất cho shot 2–5 s; nhiều hơn tốn thời gian khởi động."""
    from vidlib.common import channel  # noqa: PLC0415

    w = int(channel().get("code_render", {}).get("html_workers") or 0)
    return w or 2
