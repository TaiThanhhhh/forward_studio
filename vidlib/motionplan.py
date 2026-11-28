"""Bộ não motion (vòng 10): kho cơ chế hình ảnh, chữ ký motion mỗi video, lịch sử kênh, chống lặp khuôn giữa các video.

- **Kho cơ chế** `config/metaphors.json`: khái niệm → cơ chế cụ thể (mechanism, tiếng Anh cho LLM) + recipe (engine +
  beat/cảnh + khung params, CHỈ dùng tên có thật — `recipe_errors` đọc từ vựng engine động, không viết tay) + verbs +
  depth (lớp sâu) + avoid (sáo mòn). Recipe cần tính năng chưa có (beat mới, loài 3D/2D, verb trong engine…) khai
  `requires`; khi chưa đủ thì brief dùng `fallback` (chỉ tên đang có).
- **Khớp** `match()` theo từ khoá + dạng gốc (như styles._stems): với ý tưởng (brief) và với từng câu VO (linter).
- **Chữ ký motion** `signature()`: chuỗi beat (khung xương), bố cục, kiểu bay spine, verb, cơ chế (khai trong shot
  `"mechanism"` hoặc suy từ lời đọc), engine, look → `projects/<slug>/work/motion_signature.json` (`record`).
  Dự án cũ chưa có file: suy ra từ storyboard.json + work/code/*/job.json (bố cục + kiểu bay đã dựng thật).
- **Lịch sử kênh** `recent()`: N video SINH TRƯỚC video này (bỏ `_smoke-*`, `_*`, `cmp-*`) — chỉ video sinh trước nên chạy
  lại một dự án cũ vẫn ra cùng kết quả (tất định, RESUME giữ). Dự án sinh trước `motion.apply_since` = `legacy` (giữ
  nguyên bố cục/kiểu bay như lúc làm).
- **Chỉ số khuôn** `metrics()`: tỉ lệ beat chung chung (title/counter/compare/fact), số shot "cơ chế", độ giống khung
  xương với video gần nhất, lặp bố cục/kiểu bay/cơ chế. Ngưỡng: `config/channel.json → motion`. `lint()` cảnh báo (chặn
  khi `motion.block: true`) kèm gợi ý cơ chế thay thế; `brief_block()` = MECHANISM IDEAS + DO NOT REPEAT + verb.

CLI: `python -m vidlib.motionplan audit [--md]` · `sig <slug> [--write]` · `topic "<ý tưởng>"` · `check`.
"""
import difflib
import functools
import hashlib
import json
import os
import re
import sys
import time

from .common import CONFIG_DIR, PROJECTS, ROOT, channel, load_json, save_json

R13_MECHANISM_SCENES = ("dossier", "xray_cutaway", "hero_stat")
R13_STAGE_PRESETS = frozenset({"ecu_macro", "low_hero", "tracking_low", "over_shoulder", "dolly_zoom"})

DEFAULTS = {
    "avoid_recent": 3, "apply_since": "2026-11-20", "generic_beats": ["title", "counter", "compare", "fact"],
    "mechanism_scenes": ["scene", "drop", "process", "callout", "scale", "stage", "vectors", "units", "timeline",
                         "split", "meter", "zoomin", "dossier", "xray_cutaway", "hero_stat"],
    "flow_is_mechanism": True, "generic_max_share": 0.45, "min_mechanism_shots": 3, "skeleton_sim_max": 0.6,
    "metaphors_top_k": 6, "metaphor_min_score": 1, "shot_hint_min_score": 2, "block": False,
}
SKIP_PREFIX = ("_", ".", "cmp-")
ENGINES_DIR = os.path.join(ROOT, "engines")


def cfg():
    out = {**DEFAULTS, **{k: v for k, v in (channel().get("motion") or {}).items() if not k.startswith("_")}}
    ms = list(out.get("mechanism_scenes") or [])
    for b in R13_MECHANISM_SCENES:
        if b not in ms:
            ms.append(b)
    out["mechanism_scenes"] = ms
    return out


# ====================================================================== kho cơ chế
def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


@functools.lru_cache(maxsize=4)
def _load_metaphors(_mt):
    return load_json(os.path.join(CONFIG_DIR, "metaphors.json"), {"metaphors": []})


def library():
    return _load_metaphors(_mtime(os.path.join(CONFIG_DIR, "metaphors.json")))


def metaphors():
    return list(library().get("metaphors") or [])


def get(mid):
    return next((m for m in metaphors() if m.get("id") == mid), None)


def ids():
    return [m["id"] for m in metaphors()]


# ====================================================================== từ vựng engine (đọc động, feature-detect)
def _read(*parts):
    p = os.path.join(ENGINES_DIR, *parts)
    try:
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _header(src):
    out = []
    for ln in src.splitlines():
        if not ln.startswith("//"):
            break
        out.append(ln[2:])
    return "\n".join(out)


def _tokens(text):
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text or ""))


def _alts(text, key):
    """Mọi giá trị dạng `key: a|b|c` (hoặc `key{…}: a|b`) trong một đoạn chú thích."""
    out = set()
    for m in re.finditer(rf"\b{key}\s*:\s*([A-Za-z0-9_|\- ]+)", text or ""):
        out |= {x.strip() for x in m.group(1).split("|") if re.fullmatch(r"[A-Za-z0-9_\-]+", x.strip())}
    return out


def _obj_keys(src, marker):
    """Khoá cấp 1 của một object JS `marker = {` (đọc mã nguồn, không chạy)."""
    i = src.find(marker)
    if i < 0:
        return set()
    body, depth, j = [], 0, src.index("{", i)
    for ch in src[j:]:
        depth += ch == "{"
        depth -= ch == "}"
        body.append(ch)
        if depth == 0:
            break
    text = "".join(body)
    keys, depth, line = set(), 0, ""
    for ch in text:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        if depth == 1:
            line += ch
        if ch == "\n" or (depth == 1 and ch == ","):
            m = re.match(r"\s*,?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?\s*:", line)
            if m:
                keys.add(m.group(1))
            line = ""
    return keys


def _src_stamp():
    files = [("html", "__init__.py"), ("html", "beats.js"), ("html", "rig2d.js"), ("three", "scenes", "stage.js"),
             ("three", "creatures.js"), ("three", "main.js")]
    return tuple(_mtime(os.path.join(ENGINES_DIR, *f)) for f in files)


def vocab():
    return _vocab(_src_stamp())


@functools.lru_cache(maxsize=4)
def _vocab(_stamp):
    """Từ vựng engine thật lúc này — nguồn để validate recipe và để brief nói đúng tên (không viết tay)."""
    import lib.motion as mo  # noqa: PLC0415
    from engines import html, manim  # noqa: PLC0415

    from . import codeshot  # noqa: PLC0415
    params = {}
    for b in html.BEATS:
        req, desc = html.PARAMS.get(b, ((), ""))
        params[b] = _tokens(desc) | set(req) | {"kicker", "title", "hit", "layout", "index", "sub", "story_hud"}
    fx_html = set()
    for b in html.BEATS:
        fx_html |= _alts(html.PARAMS.get(b, ((), ""))[1], "kind")
    stage_src = _read("three", "scenes", "stage.js")
    head = _header(stage_src)
    mk = _obj_keys(stage_src, "const mk = {")
    stage_presets = _obj_keys(stage_src, "const PRESETS = {") | set(R13_STAGE_PRESETS)
    m_set = re.search(r"^ ?set:", head, flags=re.M)          # dòng "// set: …" (danh sách bối cảnh) tới "props[]:"
    i_set = m_set.start() if m_set else -1
    i_end = head.find("props[]:", max(0, i_set))
    sets = set(re.findall(r'"([a-z0-9_]+)"', head[i_set:i_end])) if i_set >= 0 and i_end > i_set else set()
    species = _alts(head, "species")
    gaits = _alts(head, "gait") | _alts(head, "gaits")
    cexpr = set()
    rig = set()
    rig_src = _read("html", "rig2d.js")
    if rig_src:
        rig = _obj_keys(rig_src, "export const SPECIES = {") or _obj_keys(rig_src, "SPECIES = {")
        if not rig:
            rig = _alts(_header(rig_src), "species")
    rig_fn = getattr(html, "rig_species", None)
    if callable(rig_fn):
        try:
            rig |= set(rig_fn())
        except Exception:  # noqa: BLE001 — feature-detect: API của WP khác có thể đang dở
            pass
    cre_src = _read("three", "creatures.js")
    if cre_src:
        species |= _obj_keys(cre_src, "export const SPECIES = {") or _obj_keys(cre_src, "SPECIES = {")
        gaits |= _js_list(cre_src, "GAITS") | _alts(_header(cre_src), "gait")
        cexpr |= _js_list(cre_src, "EXPRS") | _alts(_header(cre_src), "expr")
    from engines import adapter  # noqa: PLC0415
    cv = getattr(adapter, "creature_vocab", None)
    if callable(cv):
        try:
            v = cv() or {}
            species |= set(v.get("species") or [])
            gaits |= set(v.get("gaits") or v.get("gait") or [])
            cexpr |= set(v.get("exprs") or v.get("expr") or [])
        except Exception:  # noqa: BLE001
            pass
    return {
        "html_beats": set(html.BEATS), "html_params": params, "layouts": {k: set(v) for k, v in html.LAYOUTS.items()},
        "html_fx": fx_html, "icons": set(html.icon_table()[0]), "html_looks": set(html.LOOKS),
        "three_scenes": set(codeshot.scenes("three")), "stage_types": mk,
        "stage_tokens": _tokens(head) | {"preset", "spotlight", "fovEnd"},
        "stage_presets": stage_presets,
        "stage_sets": sets | {"black"}, "poses": _alts(head, "pose"),
        "stage_fx": _alts("\n".join(ln for ln in head.splitlines() if "fx" in ln), "kind"),
        "stage_creature": "creature" in mk or bool(re.search(r"\bcreature\b", head)),
        "rig_actions": _js_list(rig_src, "ACTIONS"), "rig_exprs": _js_list(rig_src, "EXPRS"),
        "rig_ok": bool(rig) and _rig_icon_ok(html, sorted(rig)[0]),
        "exprs": set(re.findall(r"\b([a-z]+)\b", (re.search(r"expr:\s+([a-z ]+)·", head) or [None, ""])[1]))
        | cexpr,
        "species": species, "gaits": gaits, "rig_species": rig,
        "manim_beats": set(manim.BEATS),
        "manim_params": {b: _tokens(manim.PARAMS[b][1].split(" — ")[0]) | set(manim.PARAMS[b][0]) for b in manim.BEATS},
        "verbs": set(mo.VERBS), "ease": set(mo.EASE) | {"bounce", "out", "snap", "dead", "expo"},
        "verb_support": verb_support(),
    }


def _js_list(src, name):
    m = re.search(rf"export const {name} = \[([^\]]*)\]", src or "")
    return set(re.findall(r"'([^']+)'", m.group(1))) if m else set()


def _rig_icon_ok(html, sp):
    try:
        return html.check_icon(f"rig:{sp}") is None
    except Exception:  # noqa: BLE001
        return False


def verb_support():
    """Engine nào đã chạy `do: [{verb…}]` — dò mã nguồn (WP-H2 nối html, WP-X nối three)."""
    rx = re.compile(r"\bMO\.(verb|play)\s*\(|\bplayVerbs\s*\(")
    html = bool(rx.search(_read("html", "beats.js")) or rx.search(_read("html", "core.js")))
    three = bool(rx.search(_read("three", "scenes", "stage.js")) or rx.search(_read("three", "main.js"))
                 or rx.search(_read("three", "hybrid.js")))
    return {"html": html, "three": three}


def features():
    v = vocab()
    out = {f"beat:{b}" for b in v["html_beats"]} | {f"set:{s}" for s in v["stage_sets"]}
    out |= {f"layout:{b}:{lay}" for b, ls in v["layouts"].items() for lay in ls}
    if v["species"] and v["stage_creature"]:          # loài 3D có VÀ stage đã nhận prop creature
        out.add("creatures")
    if v["rig_ok"]:                                    # loài 2D có VÀ validate html chấp nhận "rig:<loài>"
        out.add("rig2d")
    from engines import html  # noqa: PLC0415
    if re.search(r"`z`|\bz \(", html.PARAMS.get("scene", ((), ""))[1]):
        out.add("depth2d")
    for e, ok in v["verb_support"].items():
        if ok:
            out.add(f"verbs:{e}")
    return out


def requirement_met(tok, feats=None):
    feats = features() if feats is None else feats
    if tok.startswith("prop:"):
        return _stage_type_ok(tok[5:], vocab())
    return tok in feats


def _stage_type_ok(t, v):
    from engines import html  # noqa: PLC0415
    if t in v["stage_types"] or t in v["icons"] or t in v["species"]:
        return True
    ic = html.icon_for(t)
    return bool(ic and ic != "dot")


PLACEHOLDER = re.compile(r"^<[^>]+>$")
FREE_TEXT = {"text", "label", "title", "kicker", "sub", "em", "result", "teaser", "unit", "prefix", "suffix", "vs",
             "x_label", "y_label", "y_unit", "follow", "next_prefix", "side", "id", "of", "at", "from", "to", "lines",
             "labels", "tag", "t_label", "per_label", "front", "by"}
CREATURE_KEYS = {"type", "id", "species", "gait", "expr", "look", "color", "keys", "at", "rot", "scale", "hair", "face",
                 "speed", "u", "visible", "do", "heat"}
ENUM_RX = re.compile(r"\b([a-z_]+)\s*:?\s+([a-z0-9_]+(?:\|[a-z0-9_]+)+)")


def _enums(desc):
    """{tham số: {giá trị}} từ mô tả PARAMS dạng `kind ecg|battery|…`, `format year|number`, `kind: burst|…`."""
    out = {}
    for k, vals in ENUM_RX.findall(desc or ""):
        out.setdefault(k, set()).update(vals.split("|"))
    return out


def recipe_errors(rec, v=None):
    """(lỗi, cần) của một recipe: lỗi = tên không có trong engine; cần = token tính năng chưa có mà recipe dùng tới
    (beat/bố cục/loài/verb trong engine…). Tên ở chỗ tính năng chưa có không kiểm được → chỉ ghi vào `cần`."""
    import lib.motion as mo  # noqa: PLC0415
    from engines import html  # noqa: PLC0415
    v = v or vocab()
    feats = features()
    errs, needs = [], set()
    if not isinstance(rec, dict):
        return ["recipe phải là object"], needs
    eng, scene, params = rec.get("engine", "html"), rec.get("scene"), rec.get("params") or {}

    def need(tok):
        if not requirement_met(tok, feats):
            needs.add(tok)
            return False
        return True

    def check_icon(val, path):
        if isinstance(val, dict):
            e = html.check_icon(val)
            if e:
                errs.append(f"{path}: {e}")
        elif isinstance(val, str) and not PLACEHOLDER.match(val):
            if val.startswith("rig:"):
                if need("rig2d") and val[4:] not in v["rig_species"]:
                    errs.append(f"{path}: loài 2D '{val[4:]}' không có (có: {', '.join(sorted(v['rig_species']))})")
            elif val.startswith("svg:"):
                errs.append(f"{path}: recipe không dùng tài sản người dùng (svg:…) — kho cơ chế phải chạy cho mọi máy")
            elif html.icon_for(val) is None:
                errs.append(f"{path}: icon '{val}' không có trong thư viện")

    def walk(node, path, allowed, engine, enums):
        if isinstance(node, list):
            for i, x in enumerate(node):
                walk(x, f"{path}[{i}]", allowed, engine, enums)
            return
        if not isinstance(node, dict):
            return
        if "verb" in node:                            # actor/key có verb (html: actor verb+args, keys[{u, verb, dur, args}])
            need(f"verbs:{engine}")
            errs.extend(mo.verb_errors([node], where=path))
        if engine == "three" and node.get("type") == "creature":
            if not need("creatures"):
                return                                # chưa có kho loài 3D → không kiểm được tên tham số con vật
            bad = [k for k in node if k not in CREATURE_KEYS and k not in allowed]
            errs.extend(f"{path}.{k}: tham số con vật '{k}' không có" for k in bad)
        is_rig = isinstance(node.get("icon"), str) and node["icon"].startswith("rig:")
        for k, val in node.items():
            p = f"{path}.{k}"
            if k == "do":
                if engine == "html":
                    errs.append(f"{p}: engine html đọc verb ở actor (`verb`, `args`) và keys[{{u, verb, dur, args}}], "
                                "không đọc `do`")
                else:
                    need(f"verbs:{engine}")
                    errs.extend(mo.verb_errors(val, where=p))
                continue
            if k in ("verb", "dur", "args", "stagger") and "verb" in node:
                continue
            if k == "z" and engine == "html":
                need("depth2d")
                continue
            if engine == "three" and node.get("type") == "creature" and k in CREATURE_KEYS:
                pass
            elif allowed is not None and k not in allowed and k not in FREE_TEXT:
                errs.append(f"{p}: tham số '{k}' không có trong từ vựng engine")
            if isinstance(val, str) and k in enums and not PLACEHOLDER.match(val) and val not in enums[k]:
                errs.append(f"{p}: '{val}' không hợp lệ (có: {'|'.join(sorted(enums[k]))})")
            if k == "icon":
                check_icon(val, p)
            elif k == "ease" and isinstance(val, str) and val not in v["ease"]:
                errs.append(f"{p}: ease '{val}' không có")
            elif k in ("action", "expr") and engine == "html" and is_rig and isinstance(val, str):
                pool = v["rig_actions"] if k == "action" else v["rig_exprs"]
                if need("rig2d") and pool and val not in pool:
                    errs.append(f"{p}: {k} '{val}' của nhân vật 2D không có (có: {', '.join(sorted(pool))})")
            elif (k == "kind" and engine == "three" and isinstance(val, str) and re.search(r"fx\[\d+\]$", path)
                  and val not in v["stage_fx"]):
                errs.append(f"{p}: fx 3D '{val}' không có")
            elif k == "type" and engine == "three" and isinstance(val, str) and not PLACEHOLDER.match(val):
                if val != "creature" and not _stage_type_ok(val, v) and not val.startswith("model:"):
                    need(f"prop:{val}")
            elif k == "species" and engine == "three" and isinstance(val, str):
                if need("creatures") and val not in v["species"]:
                    errs.append(f"{p}: loài 3D '{val}' không có")
            elif k == "gait" and engine == "three" and isinstance(val, str):
                if need("creatures") and v["gaits"] and val not in v["gaits"]:
                    errs.append(f"{p}: gait '{val}' không có (có: {', '.join(sorted(v['gaits']))})")
            elif k == "expr" and engine == "three" and isinstance(val, str) and v["exprs"] and val not in v["exprs"]:
                errs.append(f"{p}: expr '{val}' không có")
            elif k == "pose" and engine == "three" and isinstance(val, str) and v["poses"] and val not in v["poses"]:
                errs.append(f"{p}: pose '{val}' không có")
            elif (k == "preset" and engine == "three" and isinstance(val, str) and not PLACEHOLDER.match(val)
                  and v.get("stage_presets") and val not in v["stage_presets"]):
                errs.append(f"{p}: preset camera 3D '{val}' không có (có: {', '.join(sorted(v['stage_presets']))})")
            elif k == "set" and engine == "three" and isinstance(val, str):
                need(f"set:{val}")
            if isinstance(val, (dict, list)):
                walk(val, p, allowed, engine, enums)

    if eng == "html":
        if scene not in v["html_beats"]:
            if need(f"beat:{scene}"):
                errs.append(f"beat html '{scene}' không có")
            return errs, needs
        lay = params.get("layout")
        if lay and lay not in v["layouts"].get(scene, set()):
            need(f"layout:{scene}:{lay}")
        walk(params, scene, v["html_params"][scene] | {"z"}, "html", _enums(html.PARAMS[scene][1]))
    elif eng == "three":
        if scene not in v["three_scenes"]:
            errs.append(f"cảnh three '{scene}' không có")
            return errs, needs
        allowed = (v["stage_tokens"] | {"physics", "body"}) if scene == "stage" else None
        walk(params, scene, allowed, "three", {})
    elif eng == "manim":
        from engines import manim  # noqa: PLC0415
        if scene not in v["manim_beats"]:
            errs.append(f"beat manim '{scene}' không có")
            return errs, needs
        walk(params, scene, v["manim_params"][scene], "manim", _enums(manim.PARAMS[scene][1]))
    else:
        errs.append(f"engine '{eng}' không có (three|html|manim)")
    return errs, needs


def entry_errors(m, v=None):
    """Lỗi một mục kho cơ chế: đủ trường, recipe chỉ dùng tên có thật, `requires` khai đủ, fallback chạy được ngay."""
    errs = []
    for k in ("id", "keywords", "mechanism", "recipe", "verbs", "depth", "avoid"):
        if not m.get(k):
            errs.append(f"{m.get('id', '?')}: thiếu '{k}'")
    if errs:
        return errs
    v = v or vocab()
    import lib.motion as mo  # noqa: PLC0415
    bad = [x for x in m["verbs"] if not mo.verb_name(x)]
    if bad:
        errs.append(f"{m['id']}: verbs không có: {', '.join(bad)}")
    e, needs = recipe_errors(m["recipe"], v)
    errs += [f"{m['id']}.recipe: {x}" for x in e]
    declared = set(m["recipe"].get("requires") or [])
    miss = sorted(needs - declared)
    if miss:
        errs.append(f"{m['id']}.recipe dùng tính năng chưa có mà không khai requires: {', '.join(miss)}")
    if m.get("fallback"):
        e2, needs2 = recipe_errors(m["fallback"], v)
        errs += [f"{m['id']}.fallback: {x}" for x in e2]
        if needs2:
            errs.append(f"{m['id']}.fallback phải chạy được ngay (đang cần: {', '.join(sorted(needs2))})")
    elif needs:
        errs.append(f"{m['id']}: recipe còn cần {', '.join(sorted(needs))} → thêm 'fallback' chỉ dùng tên đang có")
    d = m["depth"]
    if not isinstance(d, dict) or not any(d.get(k) for k in ("far", "mid", "near")):
        errs.append(f"{m['id']}: depth phải là {{far, mid, near}}")
    return errs


def usable_recipe(m):
    """Recipe dùng được lúc này: recipe chính nếu đủ tính năng, không thì fallback (hoặc None)."""
    _, needs = recipe_errors(m["recipe"])
    if not needs:
        return m["recipe"]
    return m.get("fallback")


# ====================================================================== khớp từ khoá (+ dạng gốc)
def _stems(text):
    from .styles import _stems as st  # noqa: PLC0415
    return st(text)


def _kw_hit(kw, stems):
    words = re.findall(r"[a-z0-9°]+", kw.lower())
    return bool(words) and all(_stems(w) & stems for w in words), len(words)


def match(text, k=None, avoid=None, penalize=None, seed=None):
    """[(id, điểm, từ khớp)] theo điểm giảm dần. avoid = {id: trọng số} bị đẩy ra sau (vẫn trả về, điểm âm);
    penalize = {id: trọng số} bị trừ nhẹ (đã gợi ý ở video trước nhưng chưa dùng)."""
    stems = _stems(str(text or "").lower())
    avoid, penalize = avoid or {}, penalize or {}
    rows = []
    for m in metaphors():
        hits, sc = [], 0.0
        for kw in m.get("keywords") or []:
            ok, n = _kw_hit(kw, stems)
            if ok:
                hits.append(kw)
                sc += n
        if not hits:
            continue
        if m.get("general"):
            sc *= 0.75                                 # cơ chế tổng quát: chỉ thắng khi khớp rõ hơn cơ chế riêng
        j = int(hashlib.sha1(f"{seed}:{m['id']}".encode()).hexdigest()[:6], 16) / 0xFFFFFF * 0.3 if seed else 0.0
        sc2 = sc + j - 1.0 * penalize.get(m["id"], 0) - (100 if avoid.get(m["id"]) else 0)
        rows.append((m["id"], round(sc2, 3), hits))
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows[:k] if k else rows


def for_topic(topic, slug=None, k=None, idea=None):
    """Top-k cơ chế cho một ý tưởng (brief): khớp từ khoá, bỏ cơ chế video gần nhất đã dùng, thiếu thì bù bằng cơ chế
    tổng quát (`general: true`) xoay theo video. Trả về [{id, score, hits, mechanism, recipe(dùng được), verbs, depth,
    avoid}]."""
    c = cfg()
    k = int(k or c["metaphors_top_k"])
    idea = idea or {}
    text = " ".join(str(x) for x in (topic, idea.get("title"), idea.get("hook"), idea.get("visual")) if x)
    used, offered = recent_mechanisms(slug), recent_offered(slug)
    rows = [r for r in match(text, avoid=used, penalize=offered, seed=slug or topic)
            if r[1] >= float(c["metaphor_min_score"]) - 100 * bool(used.get(r[0]))]
    fresh = [r for r in rows if r[1] > -50]
    stale = [r for r in rows if r[1] <= -50]
    pick = fresh[:k]
    if len(pick) < k:                                 # bù bằng cơ chế tổng quát, xoay theo video
        gen = [m for m in metaphors() if m.get("general") and m["id"] not in {p[0] for p in pick}
               and not used.get(m["id"])]
        gen.sort(key=lambda m: hashlib.sha1(f"{slug or topic}:{m['id']}".encode()).hexdigest())
        pick += [(m["id"], 0.0, []) for m in gen[: k - len(pick)]]
    if len(pick) < k:
        pick += stale[: k - len(pick)]
    out = []
    for mid, sc, hits in pick:
        m = get(mid)
        out.append({"id": mid, "score": sc, "hits": hits, "mechanism": m["mechanism"], "recipe": usable_recipe(m),
                    "verbs": m["verbs"], "depth": m["depth"], "avoid": m["avoid"], "area": m.get("area", "")})
    return out


def for_text(text, k=3, exclude=()):
    """Cơ chế hợp một câu VO / một shot (linter gợi ý thay beat chung chung)."""
    return [r for r in match(text) if r[1] >= float(cfg()["shot_hint_min_score"]) and r[0] not in exclude][:k]


# ====================================================================== chữ ký motion
def _shot_text(sh):
    p = (sh.get("code") or {}).get("params") or {}
    bits = [sh.get("vo") or "", sh.get("subject") or ""]

    def walk(x):
        if isinstance(x, dict):
            for kk, vv in x.items():
                if kk in ("text", "label", "title", "kicker", "em", "icon", "result", "sub") and isinstance(vv, str):
                    bits.append(vv)
                else:
                    walk(vv)
        elif isinstance(x, list):
            for y in x:
                walk(y)
    walk(p)
    return " ".join(bits)


def _verbs_in(x):
    import lib.motion as mo  # noqa: PLC0415
    out = []
    if isinstance(x, dict):
        if isinstance(x.get("verb"), str) and mo.verb_name(x["verb"]):
            out.append(mo.verb_name(x["verb"]))
        for v in x.values():
            out += _verbs_in(v)
    elif isinstance(x, list):
        for v in x:
            out += _verbs_in(v)
    return out


def _is_code(sh):
    mode = sh.get("mode_resolved") or sh.get("mode")
    return mode == "code" or bool((sh.get("code") or {}).get("scene") and mode != "auto")


def shot_token(sh, style):
    """Một shot → token khung xương: tên beat/cảnh code (title, counter, scene, stage…), 'flow' cho clip Flow,
    tên recipe board (doc_focus…) cho shot board."""
    from . import codeshot  # noqa: PLC0415
    c = sh.get("code") or {}
    if c.get("engine") == "board" or (not c.get("scene") and sh.get("beat_recipe") not in (None, "", "REVEAL_PHOTO")
                                       and not sh.get("start_frame", {}).get("desc")):
        return str(sh.get("beat_recipe") or "board").lower()
    if c.get("scene") and (_is_code(sh) or codeshot.is_3d(sh)):
        return c["scene"]
    return "flow"


def _engine(sh, style):
    from . import codeshot  # noqa: PLC0415
    tok = shot_token(sh, style)
    if tok == "flow":
        return "flow"
    if (sh.get("code") or {}).get("engine") == "board" or tok == str(sh.get("beat_recipe") or "").lower():
        return "board"
    try:
        return codeshot.engine_of(sh, style) or "three"
    except Exception:  # noqa: BLE001
        return "three"


def _look(style):
    from . import textstyle  # noqa: PLC0415
    try:
        st = textstyle.load_style(style)
    except Exception:  # noqa: BLE001
        return {}
    lk3 = (st.get("world") or {}).get("look3d")
    return {"html": (st.get("html") or {}).get("look", "flat"),
            "three": lk3 if isinstance(lk3, str) else (lk3 or {}).get("kind", "toon") if lk3 else "toon"}


def look_entrance(look):
    """(kiểu vào của diễn viên, kiểu vào của chữ) mặc định của một look html — đọc looks.js (chỉ đọc)."""
    src = _read("html", "looks.js")
    m = re.search(rf"^const {re.escape(look)} = \{{(.*?)^\}};", src, flags=re.M | re.S)
    body = m.group(1) if m else ""
    mo = re.search(r"motion:\s*\{[^}]*enter:\s*'(\w+)'", body)
    ty = re.search(r"type:\s*\{[^}]*enter:\s*'(\w+)'", body)
    return (mo.group(1) if mo else "pop"), (ty.group(1) if ty else "mask")


def signature(sb, style=None, jobs=None, spine_ctx=None, slug=None):
    """Chữ ký motion của một video. jobs = {sid: job.json đã dựng} (bố cục + kiểu bay thật); spine_ctx = kết quả
    codeshot.spine_context (khi chưa có job). Thiếu cả hai → bố cục ghi tay trong storyboard (nếu có)."""
    from .textstyle import canonical  # noqa: PLC0415 — id style cũ (vòng 19) → tên thể loại trong lịch sử/brief
    style = canonical(style or sb.get("style_resolved") or sb.get("style") or "forward")
    jobs, spine_ctx = jobs or {}, spine_ctx or {}
    c = cfg()
    generic, mech_sc = set(c["generic_beats"]), set(c["mechanism_scenes"])
    lk = _look(style)
    shots, moves, layouts, verbs, mechs, inferred, engines = [], [], {}, [], [], [], {}
    ids_ok = set(ids())
    for sh in sb.get("shots", []):
        tok, eng = shot_token(sh, style), _engine(sh, style)
        j = jobs.get(sh.get("id")) or {}
        p = j.get("params") if j else (sh.get("code") or {}).get("params") or {}
        lay = (p or {}).get("layout")
        sp = j.get("spine") or spine_ctx.get(sh.get("id")) or {}
        vb = sorted(set(_verbs_in((sh.get("code") or {}).get("params") or {})))
        mid = sh.get("mechanism") if sh.get("mechanism") in ids_ok else None
        inf = None
        if not mid:
            hit = for_text(_shot_text(sh), k=1)
            inf = hit[0][0] if hit else None
        is_mech = bool(mid) or tok in mech_sc or (eng == "three" and tok not in ("outro", "charsheet")) or (
            tok == "flow" and c["flow_is_mechanism"]) or (eng == "board" and tok == "silent_film")
        shots.append({"id": sh.get("id"), "beat": sh.get("beat"), "token": tok, "engine": eng, "layout": lay,
                      "move_in": sp.get("move_in"), "move_out": sp.get("move_out"), "verbs": vb, "mechanism": mid,
                      "mechanism_inferred": inf, "generic": tok in generic, "mechanism_shot": is_mech})
        engines[eng] = engines.get(eng, 0) + 1
        if lay and tok in generic | {"process"} | set(_layout_beats()):
            layouts.setdefault(tok, []).append(lay)
        if sp.get("move_out"):
            moves.append(sp["move_out"])
        verbs += vb
        if mid:
            mechs.append(mid)
        if inf:
            inferred.append(inf)
    out_job = jobs.get("OUTRO") or {}
    if (out_job.get("spine") or {}).get("move_out"):
        moves.append(out_job["spine"]["move_out"])
    skel = [s["token"] for s in shots]
    n = max(1, len(shots))
    ent_actor, ent_text = look_entrance(lk.get("html", "flat")) if engines.get("html") else (None, None)
    import lib.motion as mo  # noqa: PLC0415
    ins = sorted({v for v in verbs if mo.VERBS[v]["g"] == "in"})
    return {
        "v": 1, "slug": slug or sb.get("slug"), "topic": sb.get("topic"), "style": style, "look": lk,
        "narrative": sb.get("narrative_resolved") or sb.get("narrative"), "shots": shots, "skeleton": skel,
        "layouts": layouts, "moves": moves, "verbs": sorted(set(verbs)), "mechanisms": sorted(set(mechs)),
        "mechanisms_inferred": sorted(set(inferred)), "engines": engines,
        "entrances": sorted({x for x in (ent_actor,) if x} | set(ins)), "text_entrance": ent_text,
        "metrics": {"shots": len(shots), "generic_share": round(sum(s["generic"] for s in shots) / n, 3),
                    "mechanism_shots": sum(s["mechanism_shot"] for s in shots),
                    "verbs_distinct": len(set(verbs)), "moves_distinct": len(set(moves)),
                    "layouts_used": sum(len(v) for v in layouts.values())},
    }


def _layout_beats():
    try:
        from engines import html  # noqa: PLC0415
        return tuple(html.LAYOUTS)
    except Exception:  # noqa: BLE001
        return ()


def _proj(slug):
    return os.path.join(PROJECTS, slug)


def birth(slug):
    """Thời điểm sinh dự án (mtime nhỏ nhất của các file viết một lần lúc tạo) — None nếu chưa có dự án."""
    d = _proj(slug) if slug else None
    if not d or not os.path.isdir(d):
        return None
    ts = [os.path.getmtime(os.path.join(d, f)) for f in ("idea.txt", "idea.json", "brief.md", "plan.json",
                                                         "storyboard.json") if os.path.exists(os.path.join(d, f))]
    return min(ts) if ts else None


def _since_ts():
    try:
        return time.mktime(time.strptime(str(cfg()["apply_since"]), "%Y-%m-%d"))
    except (ValueError, TypeError):
        return 0.0


def legacy(slug):
    """Dự án sinh trước `motion.apply_since` → giữ nguyên cách chọn bố cục/kiểu bay cũ (video đã đăng không đổi hình)."""
    b = birth(slug) if slug else None
    return b is not None and b < _since_ts()


_SIG_CACHE = {}


def signature_of(slug):
    """Chữ ký motion của một dự án trên đĩa: work/motion_signature.json nếu mới hơn storyboard, không thì suy từ
    storyboard.json + work/code/*/job.json. None nếu chưa có storyboard."""
    d = _proj(slug)
    sp = os.path.join(d, "storyboard.json")
    if not os.path.exists(sp):
        return None
    code = os.path.join(d, "work", "code")
    key = (slug, _mtime(sp), _mtime(code), _mtime(os.path.join(d, "work", "motion_signature.json")))
    if key in _SIG_CACHE:
        return _SIG_CACHE[key]
    saved = os.path.join(d, "work", "motion_signature.json")
    sig = None
    if os.path.exists(saved) and _mtime(saved) >= _mtime(sp):
        sig = load_json(saved, {}) or None
    if not sig:
        sb = load_json(sp, {})
        jobs = {}
        if os.path.isdir(code):
            for sid in os.listdir(code):
                jp = os.path.join(code, sid, "job.json")
                if os.path.exists(jp):
                    jobs[sid] = load_json(jp, {})
        sig = signature(sb, jobs=jobs, slug=slug)
        pl = load_json(os.path.join(d, "plan.json"), {}) if os.path.exists(os.path.join(d, "plan.json")) else {}
        sig["offered"] = list(pl.get("mechanisms_offered") or [])
        mp = os.path.join(d, "work", "motion_plan.json")
        if os.path.exists(mp):
            sig["offered"] = list(dict.fromkeys(sig["offered"] + list(load_json(mp, {}).get("offered") or [])))
    b = birth(slug)
    sig["born"] = b
    _SIG_CACHE[key] = sig
    return sig


def record(proj, sb, style=None, jobs=None, spine_ctx=None):
    """Ghi work/motion_signature.json cho video đang làm (pipeline gọi sau khi dựng job)."""
    sig = signature(sb, style, jobs, spine_ctx, slug=os.path.basename(os.path.normpath(proj)))
    mp = os.path.join(proj, "work", "motion_plan.json")
    if os.path.exists(mp):
        sig["offered"] = list(load_json(mp, {}).get("offered") or [])
    path = os.path.join(proj, "work", "motion_signature.json")
    save_json(path, sig)
    return path


def projects():
    if not os.path.isdir(PROJECTS):
        return []
    return [s for s in os.listdir(PROJECTS) if not s.startswith(SKIP_PREFIX)
            and os.path.exists(os.path.join(PROJECTS, s, "storyboard.json"))]


def recent(slug=None, n=None):
    """Chữ ký N video sinh TRƯỚC `slug` (mới nhất trước; bỏ chính nó, _smoke-*, cmp-*)."""
    n = int(n or cfg()["avoid_recent"])
    before = birth(slug) if slug else None
    before = before if before is not None else time.time() + 1
    rows = []
    for s in projects():
        if s == slug:
            continue
        b = birth(s)
        if b is None or b >= before:
            continue
        sig = signature_of(s)
        if sig:
            rows.append((b, s, sig))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return [r[2] for r in rows[:n]]


def _weighted(sigs, fn):
    out = {}
    for i, sig in enumerate(sigs):
        w = 1.0 / (i + 1)
        for x in fn(sig):
            out[x] = round(out.get(x, 0.0) + w, 4)
    return out


def recent_moves(slug=None, sigs=None):
    sigs = recent(slug) if sigs is None else sigs
    return _weighted(sigs, lambda s: set(s.get("moves") or []))


def recent_layouts(slug=None, sigs=None):
    """{beat: {layout: trọng số gần đây}}."""
    sigs = recent(slug) if sigs is None else sigs
    out = {}
    for i, sig in enumerate(sigs):
        w = 1.0 / (i + 1)
        for beat, lays in (sig.get("layouts") or {}).items():
            for lay in set(lays):
                d = out.setdefault(beat, {})
                d[lay] = round(d.get(lay, 0.0) + w, 4)
    return out


def recent_mechanisms(slug=None, sigs=None):
    sigs = recent(slug) if sigs is None else sigs
    return _weighted(sigs, lambda s: set(s.get("mechanisms") or []) | set(s.get("mechanisms_inferred") or []))


def recent_offered(slug=None, sigs=None):
    sigs = recent(slug) if sigs is None else sigs
    return _weighted(sigs, lambda s: set(s.get("offered") or []))


LEGACY_LAYOUTS = {             # bố cục trước vòng 10 — dự án cũ chọn y như lúc làm (video đã đăng không đổi hình)
    "title": ("center", "left", "hero"), "counter": ("ring", "giant", "bar"), "compare": ("bars", "split", "balance"),
    "fact": ("center", "stamp", "left"), "process": ("list", "path"),
}


def legacy_pick_layout(scene, seed, used):
    """Đúng thuật toán + bảng bố cục của engines/html.pick_layout trước vòng 10."""
    opts = LEGACY_LAYOUTS.get(scene)
    if not opts:
        return None
    h = int(hashlib.sha1(f"{seed}:{scene}".encode()).hexdigest()[:8], 16)
    prev = used.get(scene, [])
    order = [opts[(h + len(prev) + j) % len(opts)] for j in range(len(opts))]
    pick = next((o for o in order if o not in prev), None) or next((o for o in order if not prev or o != prev[-1]),
                                                                  order[0])
    used.setdefault(scene, []).append(pick)
    return pick


def pick_layout(scene, seed, used, recent_lays, params=None):
    """Bố cục cho một shot html: tránh trước hết bố cục shot cùng beat TRONG video đã dùng, rồi bố cục các video gần
    nhất đã dùng (trọng số theo độ gần), bằng nhau thì xáo theo video. Bố cục không hợp dữ liệu shot
    (html.layout_fits, nếu có) bị bỏ. Tất định."""
    from engines import html  # noqa: PLC0415
    opts = html.LAYOUTS.get(scene)
    if not opts:
        return None
    fits = getattr(html, "layout_fits", None)
    if params is not None and callable(fits):
        opts = tuple(o for o in opts if fits(scene, o, params)) or opts[:1]
    prev = used.get(scene, [])
    hist = (recent_lays or {}).get(scene, {})

    def cost(o):
        j = int(hashlib.sha1(f"{seed}:{scene}:{o}:{len(prev)}".encode()).hexdigest()[:6], 16) / 0xFFFFFF
        return prev.count(o) * 10 + (5 if prev and prev[-1] == o else 0) + hist.get(o, 0.0) * 3 + j
    pick = min(opts, key=cost)
    used.setdefault(scene, []).append(pick)
    return pick


# ====================================================================== chỉ số khuôn
def skeleton_sim(a, b):
    """Độ giống khung xương (0..1): ½ thứ tự (SequenceMatcher) + ½ túi beat (Jaccard đa tập)."""
    if not a or not b:
        return 0.0
    seq = (difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()            # đối xứng: trung bình hai chiều
           + difflib.SequenceMatcher(None, b, a, autojunk=False).ratio()) / 2
    ca, cb = {}, {}
    for x in a:
        ca[x] = ca.get(x, 0) + 1
    for x in b:
        cb[x] = cb.get(x, 0) + 1
    keys = set(ca) | set(cb)
    bag = sum(min(ca.get(k, 0), cb.get(k, 0)) for k in keys) / max(1, sum(max(ca.get(k, 0), cb.get(k, 0)) for k in keys))
    return round(0.5 * seq + 0.5 * bag, 3)


def metrics(sig, hist):
    """Chỉ số khuôn của một video so với các video trước nó (hist: mới nhất trước)."""
    m = dict(sig.get("metrics") or {})
    sims = [(h.get("slug"), skeleton_sim(sig["skeleton"], h.get("skeleton") or [])) for h in hist]
    m["skeleton_sim"] = sims
    m["skeleton_sim_max"] = max((s for _, s in sims), default=0.0)
    last = hist[0] if hist else {}
    pairs = {(b, lay) for b, ls in (sig.get("layouts") or {}).items() for lay in ls}
    lpairs = {(b, lay) for b, ls in (last.get("layouts") or {}).items() for lay in ls}
    m["layout_reuse_last"] = round(len(pairs & lpairs) / max(1, len(pairs)), 3) if pairs else 0.0
    mv, lmv = set(sig.get("moves") or []), set(last.get("moves") or [])
    m["move_reuse_last"] = round(len(mv & lmv) / max(1, len(mv)), 3) if mv else 0.0
    me = set(sig.get("mechanisms") or []) | set(sig.get("mechanisms_inferred") or [])
    lme = set(last.get("mechanisms") or []) | set(last.get("mechanisms_inferred") or [])
    m["mechanism_reuse_last"] = sorted(me & lme)
    m["same_opening"] = bool(last) and bool(sig["skeleton"]) and sig["skeleton"][:1] == (last.get("skeleton") or [])[:1]
    return m


def _fmt_skel(sk, k=14):
    return " → ".join(sk[:k]) + (" …" if len(sk) > k else "")


def lint(sb, issue):
    """Cảnh báo khuôn lặp cho storyboard đã compile (linter gọi). issue(level, where, msg) → dict."""
    c = cfg()
    slug = sb.get("slug")
    style = sb.get("style_resolved") or sb.get("style") or "forward"
    sig = signature(sb, style, slug=slug)
    hist = recent(slug)
    m = metrics(sig, hist)
    lvl = "error" if c.get("block") else "warn"
    out = []
    topic = " ".join(str(sb.get(k) or "") for k in ("topic", "title", "hook"))
    alts = for_topic(topic, slug, k=3)
    alt_txt = "; ".join(f"`{a['id']}` ({a['mechanism'][:70]}…)" for a in alts) if alts else ""
    if m["generic_share"] > float(c["generic_max_share"]) + 1e-9:
        gen = [s["id"] for s in sig["shots"] if s["generic"]]
        out.append(issue(lvl, "motion", f"{m['generic_share']:.0%} shot là thẻ chung chung "
                         f"({'/'.join(c['generic_beats'])}: {', '.join(gen)}) > {float(c['generic_max_share']):.0%} — "
                         "đổi vài shot sang cơ chế cụ thể (diễn ra bằng hành động, không chỉ con số)"
                         + (f". Gợi ý: {alt_txt}" if alt_txt else ".")))
    if m["mechanism_shots"] < int(c["min_mechanism_shots"]):
        out.append(issue(lvl, "motion", f"Chỉ {m['mechanism_shots']} shot cho thấy CƠ CHẾ (cần ≥ "
                         f"{c['min_mechanism_shots']}: dàn cảnh tự do/3D/Flow/quá trình/cơ chế trong kho)."
                         + (f" Gợi ý: {alt_txt}" if alt_txt else "")))
    if hist and m["skeleton_sim_max"] > float(c["skeleton_sim_max"]) + 1e-9:
        who, sim = max(m["skeleton_sim"], key=lambda x: x[1])
        prev = next(h for h in hist if h.get("slug") == who)
        out.append(issue(lvl, "motion", f"Khung xương giống video '{who}' {sim:.0%} (> {float(c['skeleton_sim_max']):.0%}): "
                         f"{_fmt_skel(sig['skeleton'], 10)} ≈ {_fmt_skel(prev.get('skeleton') or [], 10)} — đổi thứ tự "
                         "beat, mở bằng beat khác, thay 1–2 thẻ bằng cơ chế."))
    if m.get("same_opening"):
        out.append(issue("info", "motion", f"Mở đầu cùng beat '{sig['skeleton'][0]}' như video trước "
                         f"('{hist[0].get('slug')}')."))
    if m.get("mechanism_reuse_last"):
        out.append(issue("info", "motion", "Cơ chế trùng video trước: " + ", ".join(m["mechanism_reuse_last"])))
    # từng shot chung chung: câu VO có cơ chế hợp hơn không
    for s, sh in zip(sig["shots"], sb.get("shots", [])):
        if s["generic"]:
            sug = for_text(_shot_text(sh), k=1)
            if sug:
                mm = get(sug[0][0])
                rec = usable_recipe(mm) or {}
                out.append(issue("info", s["id"], f"'{s['token']}' chỉ hiện con số/chữ — lời đọc hợp cơ chế "
                                 f"`{mm['id']}`: {mm['mechanism'][:90]}… (beat `{rec.get('scene', '?')}`)"))
    # verb sai tên / sai args; mechanism khai sai id
    import lib.motion as mo  # noqa: PLC0415
    known = set(ids())
    for sh in sb.get("shots", []):
        if sh.get("mechanism") and sh["mechanism"] not in known:
            near = difflib.get_close_matches(str(sh["mechanism"]), list(known), n=3, cutoff=0.5)
            out.append(issue("warn", sh.get("id", "?"), f"mechanism '{sh['mechanism']}' không có trong config/"
                             "metaphors.json" + (f" — gần: {', '.join(near)}" if near else "") + "."))
        for e in _all_verb_errors((sh.get("code") or {}).get("params") or {}, mo):
            out.append(issue("warn", sh.get("id", "?"), e))
    return out


def _all_verb_errors(params, mo):
    out = []

    def walk(x, path):
        if isinstance(x, dict):
            if isinstance(x.get("do"), list):
                out.extend(mo.verb_errors(x["do"], where=f"{path}.do"))
            if isinstance(x.get("keys"), list):
                out.extend(mo.verb_errors([k for k in x["keys"] if isinstance(k, dict) and "verb" in k],
                                          where=f"{path}.keys"))
            for k, v in x.items():
                if k not in ("do", "keys"):
                    walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
    walk(params, "params")
    return out


# ====================================================================== brief
def _recipe_txt(rec):
    if not rec:
        return ""
    r = {k: rec[k] for k in ("engine", "scene", "params") if k in rec}
    return json.dumps(r, ensure_ascii=False, separators=(", ", ": "))


def brief_block(idea, slug=None, plan=None, proj=None, idea_extra=None):
    """Đoạn brief §4c (tiếng Anh): cơ chế cho chủ đề này + không lặp khung xương video trước + verb + chiều sâu.
    proj: ghi work/motion_plan.json {offered} để video sau biết cơ chế nào đã được gợi ý."""
    import lib.motion as mo  # noqa: PLC0415

    from . import codeshot  # noqa: PLC0415
    c = cfg()
    ideas = for_topic(idea, slug, idea=idea_extra)
    hist = recent(slug)
    v = vocab()
    feats = features()
    L = ["## 4c. Motion — show the mechanism, never the same template",
         f"Every video on this channel must MOVE differently. Pick visuals from what physically happens in THIS topic. "
         f"Hard limits: at most {float(c['generic_max_share']):.0%} of shots may be generic cards "
         f"({', '.join(f'`{b}`' for b in c['generic_beats'])}); at least {c['min_mechanism_shots']} shots must SHOW a "
         "mechanism (actors acting it out, a process, a 3D action, a Flow clip). A number gets a chart only when the "
         "comparison IS the point — and then the motion must be driven by the value (a 157 bpm heart beats 157 times a "
         "minute; 70% fills 70% of the bottle; twice as fast runs twice as far).", "",
         "**MECHANISM IDEAS FOR THIS TOPIC** (from the channel's mechanism library, matched to this idea and not used in "
         "the last videos). Build 2–4 key shots on them, adapt freely, and write the id in that shot's "
         "`\"mechanism\"` field:"]
    for i, it in enumerate(ideas, 1):
        d = it["depth"]
        rec = _recipe_txt(it["recipe"])
        L.append(f"  {i}. `{it['id']}` — {it['mechanism']}"
                 + (f"\n     Recipe: `{rec}`" if rec else "")
                 + f"\n     Verbs: {', '.join(it['verbs'])} · Depth: far {d.get('far', '—')}; mid {d.get('mid', '—')}; "
                   f"near {d.get('near', '—')} · Avoid: {it['avoid']}")
    if not ideas:
        L.append("  (no library match — invent the mechanism from the facts; never fall back to number cards)")
    L.append("")
    if hist:
        L.append("**DO NOT REPEAT** — the last videos on this channel (newest first). Do not reuse their beat order, "
                 "do not open with the same beat, and do not reuse their mechanisms:")
        for h in hist:
            hm = h.get("metrics") or {}
            mech = sorted(set(h.get("mechanisms") or []) | set(h.get("mechanisms_inferred") or []))
            from .textstyle import canonical  # noqa: PLC0415 — chữ ký lưu từ trước vòng 21 có thể mang id style cũ
            L.append(f"  - `{h.get('slug')}` ({canonical(h.get('style'))}, {h.get('narrative') or 'classic'}): "
                     f"{_fmt_skel(h.get('skeleton') or [])} · generic cards {hm.get('generic_share', 0):.0%}"
                     + (f" · mechanisms: {', '.join(mech[:5])}" if mech else ""))
        lays = recent_layouts(slug, hist)
        if lays:
            L.append("  Recently used layouts (the tool rotates away from them; pick a different one if you set "
                     "`layout`): " + "; ".join(f"{b}: {', '.join(sorted(x))}" for b, x in sorted(lays.items())) + ".")
        mv = recent_moves(slug, hist)
        if mv:
            L.append(f"  Recent one-take camera moves (auto-avoided): {', '.join(sorted(mv))}.")
        fresh = []
        for b, opts in sorted(v["layouts"].items()):
            new = [o for o in sorted(opts) if not (lays.get(b) or {}).get(o)]
            if new:
                fresh.append(f"{b}: {', '.join(new)}")
        if fresh:
            L.append("  Layouts not used recently: " + "; ".join(fresh) + ".")
        L.append("")
    sup = v["verb_support"]
    L.append("**MOTION VERBS** (one vocabulary for every engine; values from the script drive them — a 157 bpm heart "
             "uses `heartbeat` with `bpm: 157`, a runner at 180 steps/min uses `bob` with `spm: 180`):")
    L.append(mo.verbs.help_text() if hasattr(mo, "verbs") else _help_fallback(mo))
    if sup["html"]:
        L.append('  html `scene` actors: a lifelong verb `"verb": "breathe", "args": {"rate": 16}` on the actor, plus '
                 'timed verbs in its keys `"keys": [{"u": 0.3, "verb": "drop_bounce", "args": {"h": 2}}, '
                 '{"u": 0.62, "verb": "squash", "dur": 0.1}]` (u = 0..1 of the shot; `dur` = how long, in u). '
                 "Put the accent verb on the VO keyword.")
    if sup["three"]:
        L.append('  3D `stage` props: `"do": [{"u": 0.5, "verb": "squash", "args": {}}]`.')
    if not sup["html"] and not sup["three"]:
        L.append("  The engines do not play verbs yet: express these motions with `keys` "
                 "(`ease`: back|bounceOut|elastic|anticip|steps…) and use the verb names as your shot plan.")
    L.append("  Every actor needs an entrance, one accent on its keyword and an idle (breathe/float/sway/bob) — never a "
             "static icon. Vary entrances inside the video (not everything `pop`).")
    depth = ("`scene` actors, labels and fx take `z` (0 = in focus, 1–4 = farther: smaller, parallax, blurred, fading "
             "into black; −0.5 = right at the lens) and the shot takes `camera` keys (dolly `z`, `rot`, `focus`)"
             if "depth2d" in feats else
             "fake it with size + alpha + order: far = small and dim, mid = the subject, near = one big prop crossing "
             "in front (enter from a frame edge, exit at the other)")
    L.append(f"**DEPTH** — layer every key shot: far / mid / near. {depth}. 3D `stage`: put a backdrop prop far "
             "behind and one prop close to the lens.")
    new_scenes = [b for b in sorted(v["html_beats"]) if b in set(c["mechanism_scenes"]) - {"scene", "stage"}]
    if new_scenes:
        L.append("**Mechanism beats available:** " + ", ".join(f"`{b}`" for b in new_scenes)
                 + " (params in §4), plus `scene` (free staging) and 3D `stage`"
                 + (" (animals: `{\"type\": \"creature\", \"species\": …}`)" if "creatures" in feats else "") + ".")
    if "rig2d" in feats:
        L.append("**2D characters:** `\"icon\": \"rig:<species>\"` (" + ", ".join(sorted(v["rig_species"])[:16]) + ").")
    _ = codeshot
    if proj:
        try:
            save_json(os.path.join(proj, "work", "motion_plan.json"),
                      {"offered": [i["id"] for i in ideas], "history": [h.get("slug") for h in hist],
                       "made": time.strftime("%Y-%m-%dT%H:%M:%S")})
        except OSError:
            pass
    return "\n".join(L)


def _help_fallback(mo):
    return "  - " + ", ".join(mo.VERBS)


# ====================================================================== audit (5 video thật) + CLI
def audit(slugs=None):
    """[(slug, chữ ký, chỉ số so với video sinh trước nó)] cho các dự án (mặc định mọi dự án thật, cũ trước)."""
    rows = []
    for s in slugs or projects():
        sig = signature_of(s)
        if sig:
            rows.append((sig.get("born") or 0, s, sig))
    rows.sort()
    out = []
    for _b, s, sig in rows:
        hist = recent(s)
        out.append((s, sig, metrics(sig, hist)))
    return out


def audit_md(rows):
    L = ["| video | style · look | narrative | khung xương (beat) | bố cục | kiểu bay spine | kiểu vào | verb | "
         "thẻ chung | shot cơ chế |", "|---|---|---|---|---|---|---|---|---|---|"]
    for s, sig, m in rows:
        lay = ", ".join(f"{b}:{'/'.join(v)}" for b, v in sorted((sig.get("layouts") or {}).items())) or "—"
        L.append(f"| `{s}` | {sig['style']} · {sig['look'].get('html')} | {sig.get('narrative') or '—'} | "
                 f"{_fmt_skel(sig['skeleton'], 16)} | {lay} | {', '.join(sig['moves']) or '—'} | "
                 f"{', '.join(sig.get('entrances') or []) or '—'} (chữ: {sig.get('text_entrance') or '—'}) | "
                 f"{m.get('verbs_distinct', 0)} | {m['generic_share']:.0%} | {m['mechanism_shots']}/{m['shots']} |")
    names = [s for s, _, _ in rows]
    L += ["", "Ma trận giống khung xương (skeleton_sim):", "", "| | " + " | ".join(f"`{n[:18]}`" for n in names) + " |",
          "|---|" + "---|" * len(names)]
    for a, sa, _ in rows:
        L.append(f"| `{a[:18]}` | " + " | ".join(f"{skeleton_sim(sa['skeleton'], sb['skeleton']):.2f}"
                                                for _, sb, _ in rows) + " |")
    return "\n".join(L)


def check_library():
    """Lỗi toàn kho (dùng cho test + `python -m vidlib.motionplan check`)."""
    v = vocab()
    errs = []
    seen = set()
    for m in metaphors():
        if m.get("id") in seen:
            errs.append(f"id trùng: {m.get('id')}")
        seen.add(m.get("id"))
        errs += entry_errors(m, v)
    return errs


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "audit"
    if cmd == "audit":
        rows = audit()
        if "--md" in argv:
            print(audit_md(rows))
        else:
            for s, sig, m in rows:
                print(f"{s}: {_fmt_skel(sig['skeleton'])} | thẻ chung {m['generic_share']:.0%} | cơ chế "
                      f"{m['mechanism_shots']}/{m['shots']} | giống video trước tối đa {m['skeleton_sim_max']:.2f} | "
                      f"bay {', '.join(sig['moves'])}")
    elif cmd == "sig" and len(argv) > 1:
        sig = signature_of(argv[1])
        if "--write" in argv and sig:
            save_json(os.path.join(_proj(argv[1]), "work", "motion_signature.json"), sig)
        print(json.dumps(sig, ensure_ascii=False, indent=1))
    elif cmd == "topic" and len(argv) > 1:
        for it in for_topic(argv[1], argv[2] if len(argv) > 2 else None):
            print(f"{it['id']} ({it['score']}): {it['mechanism']}")
    elif cmd == "check":
        errs = check_library()
        print("\n".join(errs) or f"kho cơ chế OK ({len(metaphors())} mục)")
        return 1 if errs else 0
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
