"""storyboard.json — nguồn sự thật duy nhất của một video.

Trường do người/LLM VIẾT: topic, hook, shots[].vo/onscreen/subject/camera/action/start_frame.desc/…
Trường do tool SINH (ghi đè mỗi lần chạy stage `prompts`): shots[].mode (khi "auto"), gen_sec, start_frame.prompt,
end_frame.prompt, video_prompt, ingredients[].image_prompt, thumbnail.variants[].bg_prompt, outro.bg_prompt.
Muốn tự sửa một prompt: đặt shots[].override.video_prompt (hoặc override.start_prompt / override.end_prompt).
"""
import copy
import os
import re

from .common import channel, flow_models, load_json, save_json

BEATS = ("hook", "setup", "escalate", "payoff", "twist", "outro")
MODES = ("auto", "frames_start", "frames_start_end", "ingredients", "code")
TRANSITIONS = ("cut", "flash", "whip", "match", "glitch", "fade", "dip", "iris_match", "whip_match", "tape_stop")
OUTRO_MODES = ("code", "loop", "template", "2d")
ONSCREEN_KINDS = ("caption", "label", "counter", "arrow", "circle", "tag", "compare")
ARCHETYPES = ("before_disaster", "split", "big_number", "vs", "red_circle")
ID_RE = re.compile(r"^C\d{2,3}$")
# Ngữ pháp evidence board (engine board, vòng 6) — `beat_recipe` của từng shot. Xem vidlib/boardplan.py.
RECIPES = ("REVEAL_PHOTO", "DOC_FOCUS", "NUMBER_CARD", "NAME_TAG", "CONNECT", "STAMP", "HIGHLIGHT_LINE", "THESIS",
           "NETWORK_REVEAL", "COUNTER", "TITLE_GLITCH", "SILENT_FILM")
NATIVE_RECIPES = ("DOC_FOCUS", "NUMBER_CARD", "THESIS", "NETWORK_REVEAL", "COUNTER", "TITLE_GLITCH", "SILENT_FILM")
MARK_RECIPES = ("NAME_TAG", "CONNECT", "STAMP", "HIGHLIGHT_LINE")
ASSEMBLIES = ("auto", "board_spine", "cuts")


def has_media(s):
    """Shot có hình riêng (clip Flow / cảnh three.js / ảnh người dùng) để ghim lên bảng."""
    c = s.get("code") or {}
    sf = s.get("start_frame") or {}
    if isinstance(sf, str):
        sf = {"desc": sf}
    return bool(c.get("scene") or sf.get("desc") or sf.get("seed_from") or s.get("continues_from") or s.get("action")
                or (s.get("board") or {}).get("image"))


def recipe_of(s):
    """beat_recipe tường minh, hoặc suy ra: shot có hình → REVEAL_PHOTO; thẻ board thuần → theo tham số board."""
    r = (s.get("beat_recipe") or "").upper()
    if r:
        return r
    b = s.get("board") or {}
    if b.get("old") and b.get("new"):
        return "THESIS"
    if b.get("film"):
        return "SILENT_FILM"
    if b.get("number"):
        return "NUMBER_CARD"
    if b.get("lines"):
        return "DOC_FOCUS"
    if b.get("counter") or (b.get("to") is not None and b.get("unit")):
        return "COUNTER"
    if s.get("beat") == "outro" and not has_media(s):
        return "NETWORK_REVEAL"
    return "REVEAL_PHOTO"


def board_native(s):
    """Shot dựng hoàn toàn bằng engine board (không cần clip Flow)."""
    r = recipe_of(s)
    return r in NATIVE_RECIPES or (r in MARK_RECIPES and not has_media(s))


def path_of(proj):
    return os.path.join(proj, "storyboard.json")


def load(proj):
    p = path_of(proj)
    if not os.path.exists(p):
        return None
    return load_json(p)


def save(proj, sb):
    save_json(path_of(proj), sb)


def _list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _num(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


SCHEMA_VERSION = 3


def _m1_to_2(sb):
    """v1 (trước vòng 5): không có language/style — normalize() tự đoán; chỉ đánh số."""
    return sb


def _m2_to_3(sb):
    """v3 (vòng 9): thêm `seed` (ngẫu nhiên có chủ đích của video, ghi vào manifest) nếu chưa có."""
    import hashlib  # noqa: PLC0415
    sb.setdefault("seed", int(hashlib.sha1(str(sb.get("topic", "")).encode()).hexdigest()[:8], 16))
    return sb


MIGRATIONS = {1: _m1_to_2, 2: _m2_to_3}


def migrate(sb):
    """Nâng storyboard cũ lên SCHEMA_VERSION theo từng bước (AUD-102). Trả về (sb, [bước đã chạy])."""
    v = int(sb.get("version") or 1)
    done = []
    while v < SCHEMA_VERSION:
        sb = MIGRATIONS[v](sb)
        done.append(f"v{v}→v{v + 1}")
        v += 1
    sb["version"] = max(v, int(sb.get("version") or 1))
    return sb, done


def normalize(sb, model_override=None):
    """Điền mặc định + chuẩn hoá kiểu dữ liệu. Không gọi compiler (stage `prompts` lo phần đó)."""
    sb = copy.deepcopy(sb)
    cfg = channel()
    fm = flow_models()
    sb, _ = migrate(sb)
    sb.setdefault("topic", "")
    sb.setdefault("hook", "")
    sb.setdefault("title", sb.get("topic", ""))
    if not sb.get("language"):  # dự án cũ (trước vòng 5) không có trường này → đoán từ lời đọc
        from . import lang  # noqa: PLC0415
        sb["language"] = lang.detect(s.get("vo", "") for s in _list(sb.get("shots"))) or cfg.get("language", "en")
    if "style" not in sb:   # dự án tiếng Việt cũ (không có style) giữ forward — không đổi hình video đã đăng
        sb["style"] = "forward" if str(sb["language"]).startswith("vi") else cfg.get("styles", {}).get("default", "auto")
    sb.setdefault("voice", "auto")
    sb.setdefault("cues", [])
    sb.setdefault("assembly", "auto")
    pub = sb.setdefault("publish", {})
    pub.setdefault("titles", [])
    pub.setdefault("description", "")
    pub.setdefault("hashtags", [])
    f = sb.setdefault("format", {})
    f.setdefault("aspect", cfg["format"]["aspect"])
    f.setdefault("fps", cfg["format"]["fps"])
    f.setdefault("target_sec", cfg["duration"]["target_sec"])
    fl = sb.setdefault("flow", {})
    fl.setdefault("image_model", cfg["flow"].get("image_model") or fm.get("default_image_model"))
    fl.setdefault("video_model", cfg["flow"].get("video_model") or fm.get("default_video_model"))
    if model_override:
        fl["video_model"] = model_override
    for k, ing in enumerate(_list(sb.get("ingredients"))):
        ing.setdefault("id", f"REF_{k + 1}")
        ing.setdefault("desc", "")
        ing.setdefault("accent_on", "")
        ing.setdefault("file", f"refs/{ing['id']}.png")
    sb["ingredients"] = _list(sb.get("ingredients"))
    shots = _list(sb.get("shots"))
    for i, s in enumerate(shots):
        s.setdefault("id", f"C{i + 1:02d}")
        s["id"] = str(s["id"]).upper()
        if re.match(r"^C\d$", s["id"]):
            s["id"] = f"C0{s['id'][1]}"
        s.setdefault("beat", "hook" if i == 0 else "escalate")
        s.setdefault("vo", "")
        s["onscreen"] = [o if isinstance(o, dict) else {"text": str(o)} for o in _list(s.get("onscreen"))]
        for o in s["onscreen"]:
            o.setdefault("kind", "caption")
            o["t"] = _num(o.get("t"), 0.0)
        s["target_sec"] = _num(s.get("target_sec"), 2.0)
        s.setdefault("gen_sec", None)
        s.setdefault("mode", "auto")
        s.setdefault("state_change", False)
        s.setdefault("continues_from", None)
        s.setdefault("layout_free", False)
        s["refs"] = _list(s.get("refs"))
        s.setdefault("subject", "")
        s.setdefault("camera", "Locked-off static shot")
        s.setdefault("action", [])
        if isinstance(s["action"], str):
            s["action"] = [{"t": None, "do": s["action"]}]
        s.setdefault("accent_on", "")
        sf = s.setdefault("start_frame", {})
        if isinstance(sf, str):
            sf = s["start_frame"] = {"desc": sf}
        sf.setdefault("desc", "")
        sf.setdefault("prompt", "")
        sf.setdefault("file", f"frames/{s['id']}_start.png")
        sf.setdefault("seed_from", None)
        if s.get("continues_from") and not sf.get("seed_from"):
            sf["seed_from"] = s["continues_from"]
        ef = s.get("end_frame") or {}
        if isinstance(ef, str):
            ef = {"desc": ef}
        ef.setdefault("desc", "")
        ef.setdefault("prompt", "")
        ef.setdefault("file", f"frames/{s['id']}_end.png")
        s["end_frame"] = ef
        s.setdefault("video_prompt", "")
        tr = s.setdefault("trim", {})
        tr.setdefault("in", None)
        tr.setdefault("out", None)
        tr["speed"] = _num(tr.get("speed"), 1.0)
        s.setdefault("transition_in", "cut")
        s["sfx"] = [x if isinstance(x, str) else x.get("name", "") for x in _list(s.get("sfx"))]
        s["punch_in"] = [float(x) for x in _list(s.get("punch_in"))]
        s.setdefault("override", {})
        s["avoid_drop"] = _list(s.get("avoid_drop"))
        s.setdefault("code", None)
        s.setdefault("beat_recipe", None)
        s["board"] = s.get("board") or {}
        if s["beat_recipe"]:
            s["beat_recipe"] = str(s["beat_recipe"]).upper()
        img_only = s["board"].get("image") and not (s.get("start_frame") or {}).get("desc") and not s.get("action")
        if (board_native(s) or img_only) and not (s.get("code") or {}).get("scene"):
            s["mode"] = "code"  # thẻ board thuần: engine board vẽ, không cần Flow
            s["code"] = {**(s.get("code") or {}), "engine": "board"}
        s.setdefault("hold", False)  # true = được phép đứng hình có chủ đích (QA không bắt freeze)
        s.setdefault("clip_file", f"clips/{s['id']}.mp4")
    sb["shots"] = shots
    o = sb.setdefault("outro", {})
    o.setdefault("enabled", cfg["outro"]["enabled"])
    o.setdefault("loop", cfg["outro"]["loop"])
    o.setdefault("teaser", "")
    from . import lang  # noqa: PLC0415
    o.setdefault("follow_text", lang.copy("follow"))
    o.setdefault("mode", "code" if cfg["outro"].get("code", True) else "2d")
    if o.get("mode") == "loop":
        o["loop"] = True
        o.setdefault("bridge_frames", 8)
    o.setdefault("params", {})
    th = sb.setdefault("thumbnail", {})
    th["variants"] = _list(th.get("variants"))
    for k, v in enumerate(th["variants"]):
        v.setdefault("id", f"T{k + 1}")
        v.setdefault("archetype", ARCHETYPES[k % len(ARCHETYPES)])
        v.setdefault("text", "")
        v.setdefault("scene", "")
        v.setdefault("focus", [0.5, 0.45])
        v.setdefault("file", f"thumbnails/bg_{v['id']}.png")
    sb.setdefault("caption", "")
    sb.setdefault("hashtags", [])
    return sb


def validate(sb):
    """Kiểm tra cấu trúc. Trả về (errors, warnings) — chuỗi tiếng Việt."""
    errs, warns = [], []
    if not isinstance(sb, dict):
        return ["storyboard.json phải là một object JSON."], []
    for k in ("topic", "shots"):
        if not sb.get(k):
            errs.append(f"Thiếu trường '{k}'.")
    models = flow_models().get("video_models", {})
    vm = sb.get("flow", {}).get("video_model")
    if vm and vm not in models:
        errs.append(f"Model video '{vm}' không có trong config/flow-models.json. Có: {', '.join(models)}.")
    ids = [s.get("id") for s in sb.get("shots", [])]
    if len(set(ids)) != len(ids):
        errs.append("Có id shot bị trùng.")
    ing_ids = {i.get("id") for i in sb.get("ingredients", [])}
    seen = set()
    for s in sb.get("shots", []):
        tag = s.get("id", "?")
        if not ID_RE.match(str(tag)):
            errs.append(f"{tag}: id phải dạng C01, C02…")
        if s.get("beat") not in BEATS:
            errs.append(f"{tag}: beat '{s.get('beat')}' không hợp lệ ({'|'.join(BEATS)}).")
        if s.get("mode") not in MODES:
            errs.append(f"{tag}: mode '{s.get('mode')}' không hợp lệ ({'|'.join(MODES)}). Text-to-video không được dùng.")
        if s.get("transition_in") not in TRANSITIONS:
            errs.append(f"{tag}: transition_in '{s.get('transition_in')}' không hợp lệ ({'|'.join(TRANSITIONS)}).")
        for r in s.get("refs", []):
            if r not in ing_ids:
                errs.append(f"{tag}: ref '{r}' không có trong ingredients.")
        cf = s.get("continues_from") or s.get("start_frame", {}).get("seed_from")
        if cf and cf not in seen:
            errs.append(f"{tag}: continues_from/seed_from '{cf}' phải là một shot ĐỨNG TRƯỚC.")
        board_eng = (s.get("code") or {}).get("engine") == "board"
        if s.get("beat_recipe") and s["beat_recipe"] not in RECIPES:
            errs.append(f"{tag}: beat_recipe '{s['beat_recipe']}' không hợp lệ ({'|'.join(RECIPES)}).")
        if (s.get("mode") == "code" and not s.get("code")) or (s.get("code") and not s["code"].get("scene")
                                                                 and not board_eng):
            errs.append(f"{tag}: shot code cần 'code': {{'scene': '<engine/scenes/*.js>', 'params': {{...}}}} "
                        "(ý tưởng mới: scene 'stage').")
        from . import textfx  # noqa: PLC0415 — chữ trong cảnh: behavior/anchor/layer/vật tham chiếu hợp lệ
        errs += textfx.validate_fx(s, textfx.shot_objects(sb, s))
        if s.get("code") and s["code"].get("scene"):
            from . import codeshot  # noqa: PLC0415
            eng = s["code"].get("engine")
            if eng and eng not in ("three", "html", "manim", "board"):
                errs.append(f"{tag}: code.engine '{eng}' không hợp lệ (three|html|manim|board).")
            else:
                eng = codeshot.engine_of(s, sb.get("style_resolved") or sb.get("style"))
                if s["code"]["scene"] not in codeshot.scenes(eng):
                    errs.append(f"{tag}: engine {eng} không có cảnh/beat '{s['code']['scene']}' "
                                f"(có: {', '.join(codeshot.scenes(eng))}).")
                elif eng == "three":
                    from engines.adapter import validate_three  # noqa: PLC0415
                    errs += [f"{tag}: {m}" for m in validate_three(s["code"]["scene"], s["code"].get("params"))]
                elif eng in ("html", "manim"):
                    import importlib  # noqa: PLC0415
                    errs += [f"{tag}: {m}" for m in importlib.import_module(f"engines.{eng}").validate(
                        s["code"]["scene"], s["code"].get("params"))]
        if board_eng:
            from . import boardplan  # noqa: PLC0415
            errs += boardplan.validate_shot(s)
        elif not s.get("code"):
            if not (s.get("start_frame", {}).get("desc") or cf or s.get("mode") == "ingredients"):
                errs.append(f"{tag}: thiếu start_frame.desc (mô tả ảnh khung đầu).")
            if not s.get("action"):
                errs.append(f"{tag}: thiếu action (hành động trong clip).")
        if (s.get("target_sec") or 0) <= 0:
            errs.append(f"{tag}: target_sec phải > 0.")
        for o in s.get("onscreen", []):
            if o.get("kind") not in ONSCREEN_KINDS:
                errs.append(f"{tag}: onscreen kind '{o.get('kind')}' không hợp lệ ({'|'.join(ONSCREEN_KINDS)}).")
            if o.get("t", 0) < 0 or o.get("t", 0) > (s.get("target_sec") or 0) + 0.01:
                warns.append(f"{tag}: chữ '{o.get('text', '')}' có t={o.get('t')} nằm ngoài shot ({s.get('target_sec')}s).")
        if "story_hud" in s and s["story_hud"] is not None and not isinstance(s["story_hud"], (dict, bool)):
            errs.append(f"{tag}: story_hud phải là object JSON hoặc false/null.")
        seen.add(tag)
    if sb.get("assembly", "auto") not in ASSEMBLIES:
        errs.append(f"assembly '{sb.get('assembly')}' không hợp lệ ({'|'.join(ASSEMBLIES)}).")
    om = (sb.get("outro") or {}).get("mode")
    if om and om not in OUTRO_MODES:
        errs.append(f"outro.mode '{om}' không hợp lệ ({'|'.join(OUTRO_MODES)}).")
    if "archetype" in sb and sb["archetype"] is not None:
        if not isinstance(sb["archetype"], str):
            errs.append("archetype phải là chuỗi (hoặc 'auto'/null).")
        elif sb["archetype"] != "auto":
            from . import narratives  # noqa: PLC0415
            if sb["archetype"] not in narratives.archetype_ids():
                warns.append(f"archetype '{sb['archetype']}' không có trong config/archetypes.json "
                             f"(có: {', '.join(narratives.archetype_ids())}).")
    if "format_family" in sb and sb["format_family"] is not None:
        if not isinstance(sb["format_family"], str):
            errs.append("format_family phải là chuỗi (hoặc 'auto'/null).")
        elif sb["format_family"] != "auto":
            from . import narratives  # noqa: PLC0415
            if sb["format_family"] not in narratives.format_ids():
                warns.append(f"format_family '{sb['format_family']}' không có trong config/formats.json "
                             f"(có: {', '.join(narratives.format_ids())}).")
    if "story_hud" in sb and sb["story_hud"] is not None and not isinstance(sb["story_hud"], (dict, bool)):
        errs.append("story_hud phải là object JSON hoặc false/null.")
    for v in sb.get("thumbnail", {}).get("variants", []):
        if v.get("archetype") not in ARCHETYPES:
            errs.append(f"Thumbnail {v.get('id')}: archetype '{v.get('archetype')}' không hợp lệ ({'|'.join(ARCHETYPES)}).")
    return errs, warns


def shot(sb, sid):
    for s in sb["shots"]:
        if s["id"] == sid:
            return s
    return None


