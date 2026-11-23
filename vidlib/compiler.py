"""Prompt compiler: ghép prompt Flow từ các block cố định trong prompts/blocks/*.txt.

Không viết tay prompt dài cho từng cảnh. Mỗi shot chỉ mô tả NGỮ NGHĨA (subject, trạng thái, camera, hành động);
compiler lo style lock, bố cục, accent, motion/style/audio/avoid, và chọn mode Frames/Ingredients theo
capability của model trong config/flow-models.json.

Nguyên tắc vàng: Ingredients dùng ở bước tạo ẢNH (đưa ảnh ref vào image model khi tạo start/end frame),
Frames dùng ở bước tạo VIDEO. Text-to-video thuần không bao giờ được dùng.
"""
import copy
import re

from .common import block, brand, ceil_to, channel, flow_models

FRAME_CONSTRAINT = {
    "frames_start": "Starts exactly on the provided start frame.",
    "frames_start_seed": "Starts exactly on the provided start frame and continues that motion instantly, without pause.",
    "frames_start_end": "Starts exactly on the provided start frame and ends exactly on the provided end frame.",
}
MODE_LABEL = {
    "frames_start": "FRAMES · Start",
    "frames_start_end": "FRAMES · Start+End",
    "ingredients": "INGREDIENTS",
    "code": "ĐỒ HOẠ CODE",
}

THUMB_LAYOUT = {
    "before_disaster": {
        "16:9": "The subject sits in the left 55% of the frame at the exact instant BEFORE disaster; keep the right 40% "
                "as empty black space.",
        "9:16": "The subject sits in the lower-middle at the exact instant BEFORE disaster; keep the top 30% as empty "
                "black space.",
    },
    "split": {
        "16:9": "Split composition: the left half shows the BEFORE state clearly; the right half is mostly empty black.",
        "9:16": "Split composition: the top half shows the BEFORE state clearly; the bottom half is mostly empty black.",
    },
    "big_number": {
        "16:9": "One small subject placed low on the right third, about 30% of frame height; huge empty black space on "
                "the left.",
        "9:16": "One small subject placed low-center, about 30% of frame height; huge empty black space above it.",
    },
    "vs": {
        "16:9": "Two opposing subjects face each other from the left and right edges, bright sparks colliding at the "
                "exact center.",
        "9:16": "Two opposing subjects face each other from the top and bottom, bright sparks colliding at the exact "
                "center.",
    },
    "red_circle": {
        "16:9": "The subject is centered and large; one small unusual detail is clearly visible and isolated.",
        "9:16": "The subject is centered and large; one small unusual detail is clearly visible and isolated.",
    },
}


# ------------------------------------------------------------------ capability
def video_caps(sb):
    name = sb["flow"]["video_model"]
    return name, flow_models()["video_models"][name]


def image_caps(sb):
    name = sb["flow"]["image_model"]
    return name, flow_models().get("image_models", {}).get(name, {"max_refs": 1})


def supports(caps, mode):
    fr = caps.get("frames", "none")
    if mode == "frames_start":
        return fr in ("first", "first_last")
    if mode == "frames_start_end":
        return fr == "first_last"
    if mode == "ingredients":
        return (caps.get("ingredients_max") or 0) > 0
    return False


def choose_mode(shot, caps):
    """Trả về (mode, lý do tiếng Việt). Quy tắc theo bảng trong docs/PLAN.md (R4)."""
    if shot.get("code") or shot.get("mode") == "code":
        why = shot.get("code", {}).get("auto_reason") if shot.get("code") else None
        return "code", why or "Shot dựng bằng code (engine three.js / đồ hoạ 2D), không cần Flow."
    want = shot.get("mode", "auto")
    seed = shot.get("start_frame", {}).get("seed_from")
    if want != "auto":
        if supports(caps, want):
            return want, "Chỉ định trong storyboard."
        fb = "frames_start"
        return fb, f"Model không hỗ trợ {want} → dùng {fb}."
    if seed:
        return "frames_start", f"Cảnh nối tiếp {seed}: ảnh Start lấy từ cuối clip {seed} để chuyển cảnh liền mạch."
    if shot.get("state_change"):
        if supports(caps, "frames_start_end"):
            return "frames_start_end", "Biến đổi trạng thái trước → sau: khoá cả frame cuối."
        return "frames_start", "Biến đổi trạng thái nhưng model không có last frame → chỉ khoá start."
    refs = shot.get("refs") or []
    if refs and shot.get("layout_free") and supports(caps, "ingredients") \
            and len(refs) <= (caps.get("ingredients_max") or 0):
        return "ingredients", "Nhân vật/đạo cụ lặp lại, bố cục tự do: giữ nhất quán bằng Ingredients."
    return "frames_start", "Mặc định: ảnh start khoá style 2D và bố cục, chống trôi phong cách."


def allowed_durations(caps, mode=None):
    """Độ dài hợp lệ cho mode: first+last bị giới hạn (Omni 1.2: ≤10s)."""
    durs = sorted(caps.get("durations_sec") or [8])
    if mode == "frames_start_end" and caps.get("first_last_max_sec"):
        durs = [d for d in durs if d <= caps["first_last_max_sec"]] or durs[:1]
    return durs


def gen_seconds(shot, caps, margin=None, mode=None):
    """Độ dài clip cần chọn trong Flow: ≥ target × speed + margin, làm tròn lên độ dài hợp lệ của model.
    Ưu tiên ≤ preferred_max_sec (Omni: giây 11–15 tính gấp đôi credit)."""
    margin = channel()["flow"]["gen_margin_sec"] if margin is None else margin
    need = shot["target_sec"] * float(shot.get("trim", {}).get("speed") or 1.0) + margin
    durs = allowed_durations(caps, mode or shot.get("mode_resolved"))
    pref = [d for d in durs if d <= (caps.get("preferred_max_sec") or durs[-1])]
    if pref and pref[-1] >= need:
        return ceil_to(pref, need)
    return ceil_to(durs, need)


# ------------------------------------------------------------------ helpers
def _sent(x):
    x = " ".join(str(x or "").split()).strip()
    if not x:
        return ""
    x = x[0].upper() + x[1:]
    return x if x[-1] in ".!?" else x + "."


def _cap(x):
    """Viết hoa chữ đầu, bỏ dấu chấm cuối (để chèn vào chỗ '{x}.' trong block)."""
    x = " ".join(str(x or "").split()).strip().rstrip(".")
    return x[:1].upper() + x[1:]


def _is_3d_flow(fs):
    return bool(fs and (fs.get("is_3d") or "3d" in (fs.get("medium") or "").lower()))


def avoid_block(shot, sb=None):
    """Block AVOID cố định, bỏ các mục mâu thuẫn với chính cảnh đó (shot.avoid_drop) hoặc style 3D."""
    drop = {d.strip().lower() for d in (shot or {}).get("avoid_drop") or []}
    fs = flow_style(sb)
    if _is_3d_flow(fs):
        drop |= {"3d shading", "3d render"}
    if fs and fs.get("avoid_drop"):
        drop |= {d.strip().lower() for d in fs["avoid_drop"]}
    add = [a.strip() for a in (fs or {}).get("avoid_add") or [] if a.strip()]
    if not drop and not add:
        return block("avoid")
    head, _, items = block("avoid").partition(":")
    keep = [i.strip() for i in items.rstrip(".").split(",") if i.strip().lower() not in drop]
    keep += [a for a in add if a.lower() not in {k.lower() for k in keep}]
    return f"{head}: {', '.join(keep)}."


def motion_text(sb=None):
    """Block MOTION: câu đầu cố định (chuyển động từ frame đầu tới frame cuối, không lắng) + `flow.motion_block` ngắn
    của style nếu có (preset atlas), không thì nguyên block mặc định."""
    base = block("motion")
    mb = (flow_style(sb) or {}).get("motion_block")
    if not mb:
        return base
    head = base.split(". ", 1)[0].rstrip(".") + "."
    return f"{head} {' '.join(str(mb).split())}"


def plate_text(sb=None):
    """Chỗ trống cho chữ (ribbon/cờ/bảng) — chữ luôn do text_fx/engine thêm sau, Flow chỉ vẽ mặt trống."""
    pl = (flow_style(sb) or {}).get("plate")
    return f"Leave {' '.join(str(pl).split())} empty (captions are added later)." if pl else ""


def accent_kw(sb=None):
    """Accent riêng của style (preset atlas: `flow.accent` + `flow.accent_name`) thay accent brand trong block ảnh."""
    fs = flow_style(sb) or {}
    return {"accent": fs["accent"], "accent_name": fs["accent_name"]} if fs.get("accent") and fs.get("accent_name") else {}


def _clause(x):
    """Bỏ dấu chấm cuối và chữ hoa đầu để chèn giữa câu."""
    x = " ".join(str(x or "").split()).strip().rstrip(".")
    return x[:1].lower() + x[1:] if x[:2] != x[:2].upper() else x


def _num(v):
    v = float(v)
    return f"{int(round(v))}" if abs(v - round(v)) < 1e-6 else f"{v:.1f}"


def timestamp(a, b, style="veo"):
    """Omni: [0-1.5s] · Veo: [00:00-00:01.5] (theo hướng dẫn prompt chính thức của từng model)."""
    if style == "omni":
        return f"[{_num(a)}-{_num(b)}s]"
    return f"[00:{float(a):05.2f}-00:{float(b):05.2f}]".replace(".00", "")


def action_text(shot, style="veo"):
    parts = []
    for a in shot.get("action") or []:
        if isinstance(a, str):
            parts.append(_sent(a))
            continue
        do = _sent(a.get("do", ""))
        t = a.get("t")
        if isinstance(t, (list, tuple)) and len(t) == 2:
            parts.append(f"{timestamp(t[0], t[1], style)} {do}")
        else:
            parts.append(do)
    return " ".join(p for p in parts if p)


def _colors():
    b = brand()
    return {"bg": b["colors"]["bg"], "accent": b["colors"]["accent"], "accent_name": b["accent_name"],
            "danger": b["colors"]["danger"], "danger_name": b["danger_name"]}


def _fill(name, **kw):
    vals = {**_colors(), **kw}
    return block(name).format(**vals)


DEFAULT_CAMERA = "Locked-off static shot"   # = storyboard.normalize mặc định
BRAND_MEDIUM = "Flat 2D vector"
BRAND_LOOK = "Bold clean white outlines, uniform line weight, flat white/grey fills"
BRAND_LOOK_THUMB = "Bold thick white outlines, flat white/grey fills"


def flow_style(sb):
    """Khối `flow` của style video (styles/<style>.json): {"medium", "look"} — None = look brand mặc định."""
    name = (sb or {}).get("style_resolved") or (sb or {}).get("style")
    if not name or name == "auto":
        return None
    from . import textstyle  # noqa: PLC0415
    try:
        return textstyle.load_style(name).get("flow")
    except Exception:  # noqa: BLE001 — style chưa có/không hợp lệ: storyboard.validate báo
        return None


def stylize(text, sb):
    """Đổi chất liệu trong prompt Flow theo style (giữ nguyên nền đen, accent, bố cục, AVOID). forward → không đổi."""
    fs = flow_style(sb)
    if not fs or not text:
        return text
    if fs.get("medium"):
        text = text.replace(BRAND_MEDIUM, fs["medium"])
    if fs.get("look"):
        text = text.replace(BRAND_LOOK, fs["look"]).replace(BRAND_LOOK_THUMB, fs["look"])
    if _is_3d_flow(fs):
        text = text.replace(", 3D render", "").replace(", 3D shading", "")
        text = text.replace(
            "Same line weight and palette throughout.",
            "Same 3D material shading, lighting, and palette throughout.",
        )
    return text


def refs_for(sb, ids):
    by = {i["id"]: i for i in sb.get("ingredients", [])}
    return [by[r] for r in ids if r in by]


# ------------------------------------------------------------------ prompt ảnh
def frame_prompt(sb, shot, which="start"):
    fr = shot.get(f"{which}_frame") or {}
    desc = fr.get("desc", "")
    if not desc:
        return ""
    ov = (shot.get("override") or {}).get(f"{which}_prompt")
    if ov:
        return ov
    accent_on = shot.get("accent_on") or "the single key element"
    refs = refs_for(sb, shot.get("refs") or [])
    ref_txt = ""
    if refs:
        names = "; ".join(f"{r['id']} = {_clause(r['desc'])}" for r in refs)
        ref_txt = (f"Use the attached reference image{'s' if len(refs) > 1 else ''} ({names}) and keep "
                   f"{'their' if len(refs) > 1 else 'its'} exact design. ")
    parts = [
        _fill("frame_style"),
        _sent(desc),
        block("frame_layout"),
        _fill("frame_look", accent_on=_clause(accent_on), **accent_kw(sb)),
        plate_text(sb),
        ref_txt.strip(),
        block("frame_avoid"),
    ]
    return stylize(" ".join(p for p in parts if p), sb)


def ingredient_prompt(sb, ing):
    return _ingredient_raw(sb, ing) if not flow_style(sb) else stylize(_ingredient_raw(sb, ing), sb)


def _ingredient_raw(sb, ing):
    return _fill("ingredient", desc=_cap(ing.get("desc", "")),
                 accent_on=_clause(ing.get("accent_on") or "one small key detail"))


# ------------------------------------------------------------------ prompt video
def video_prompt(sb, shot, mode=None):
    ov = (shot.get("override") or {}).get("video_prompt")
    if ov:
        return ov
    mode = mode or shot.get("mode_resolved") or shot.get("mode")
    seed = shot.get("start_frame", {}).get("seed_from")
    _, caps = video_caps(sb)
    # Omni mặc định tạo video NHIỀU cảnh → luôn yêu cầu một shot liên tục (aistudio.google.com/docs/omni).
    cam = shot.get("camera") or ""
    if cam in ("", DEFAULT_CAMERA) and (flow_style(sb) or {}).get("camera"):      # shot không ghi camera → camera của style
        cam = flow_style(sb)["camera"]
    cam = cam or DEFAULT_CAMERA
    lines = ["Single continuous shot. " + _sent(cam)]
    if mode == "ingredients":
        scene = _sent(shot.get("start_frame", {}).get("desc", ""))
        if scene:
            lines.append(scene)
    lines.append(action_text(shot, caps.get("timestamp_style", "veo")))
    if mode == "ingredients":
        names = ", ".join(r["id"] for r in refs_for(sb, shot.get("refs") or []))
        lines.append(f"Keep the exact design of the provided ingredient images ({names}).")
        match = "the provided ingredient images"
    else:
        key = "frames_start_seed" if (mode == "frames_start" and seed) else mode
        lines.append(FRAME_CONSTRAINT.get(key, FRAME_CONSTRAINT["frames_start"]))
        match = "the start frame"
    lines += [motion_text(sb), _fill("style", match_target=match), block("audio"), avoid_block(shot, sb)]
    return stylize("\n".join(x for x in lines if x), sb)


def scene_part(prompt):
    """Phần mô tả cảnh (trước các block cố định) — dùng cho linter."""
    m = prompt.find(block("motion")[:40])
    return prompt[:m] if m > 0 else prompt


# ------------------------------------------------------------------ prompt khác
def style_bible(sb=None):
    b = brand()
    c = b["colors"]
    fs = flow_style(sb)
    if _is_3d_flow(fs):
        med = fs.get("medium") or "Stylized 3D clay diorama"
        lk = fs.get("look") or "Smooth matte clay surfaces, studio rim light, soft shadows"
        return "\n".join([
            "STYLE BIBLE — channel \"" + channel()["name"] + "\" (paste before any image prompt if Flow drifts)",
            f"- Format: {med} animation, 9:16 vertical, pure solid black background ({c['bg']}), no gradient, "
            f"no background clutter.",
            f"- Look & Shading: {lk}.",
            f"- Accent: ONE color only — {b['accent_name']} ({c['accent']}) on the single key element; "
            f"{b['danger_name']} ({c['danger']}) only for explosions or warnings.",
            f"- Characters: {b['character']}.",
            f"- Signature motif: {b['motif']}.",
            "- Motion: snappy stop-motion / stylized 3D timing, quick anticipation, fast action, slight overshoot, "
            "tactile squash-and-stretch. No floaty slow motion.",
            "- Layout: subject centered, ~55% of frame; top 12% and bottom 30% empty for captions.",
            "- Never draw text, letters, numbers, logos or watermarks (all text is added in post).",
        ])
    return "\n".join([
        "STYLE BIBLE — channel \"" + channel()["name"] + "\" (paste before any image prompt if Flow drifts)",
        f"- Format: flat 2D vector animation, 9:16 vertical, pure solid black background ({c['bg']}), no gradient, "
        f"no texture.",
        f"- Lines: bold clean white ({c['ink']}) outlines, uniform line weight, square line caps.",
        f"- Fills: flat white and grey ({c['fill']}) only.",
        f"- Accent: ONE color only — {b['accent_name']} ({c['accent']}) on the single key element; "
        f"{b['danger_name']} ({c['danger']}) only for explosions or warnings.",
        f"- Characters: {b['character']}.",
        f"- Signature motif: {b['motif']}.",
        "- Motion: snappy cartoon timing, quick anticipation, fast action, slight overshoot, squash-and-stretch, "
        "smear frames. No floaty slow motion.",
        "- Layout: subject centered, ~55% of frame; top 12% and bottom 30% empty for captions.",
        "- Never draw text, letters, numbers, logos or watermarks (all text is added in post).",
    ])


def thumbnail_prompt(sb, v, aspect="16:9"):
    arch = v.get("archetype", "before_disaster")
    layout = THUMB_LAYOUT.get(arch, THUMB_LAYOUT["before_disaster"])[aspect]
    danger = ""
    if arch in ("before_disaster", "red_circle"):
        danger = f", plus {brand()['danger_name']} ({brand()['colors']['danger']}) only on the danger element"
    ar = "16:9 horizontal" if aspect == "16:9" else "9:16 vertical"
    refs = refs_for(sb, v.get("refs") or [])
    ref_txt = (" Use the attached reference images and keep their exact design.") if refs else ""
    p = _fill("thumbnail_bg", aspect=ar, scene=_cap(v.get("scene") or sb.get("hook") or sb.get("topic")),
              layout=layout, danger=danger)
    return stylize(p + ref_txt + " " + block("frame_avoid"), sb)


def outro_prompt(sb=None):
    return stylize(_fill("outro_bg") + "\n" + block("audio") + "\n" + block("avoid"), sb)


# ------------------------------------------------------------------ compile
def compile_all(sb, auto_code_ids=None):
    """Trả về bản storyboard đã có mode/gen_sec/prompt (không sửa bản gốc).
    auto_code_ids: shot chưa có clip Flow — nếu là loại cảnh Flow làm kém (cân, nhiệt kế, đồng hồ đo, outro…) và
    engine có cảnh tương ứng thì TỰ CHỌN mode code."""
    from . import codeshot  # noqa: PLC0415
    sb = copy.deepcopy(sb)
    _, caps = video_caps(sb)
    for s in sb["shots"]:
        if auto_code_ids and s["id"] in auto_code_ids and s.get("mode", "auto") == "auto" and not s.get("code"):
            scene, why = codeshot.suggest(s)
            if scene:
                s["code"] = {"scene": scene, "params": {}, "auto_reason": f"Tự chọn code: {why}."}
    for s in sb["shots"]:
        mode, why = choose_mode(s, caps)
        s["mode_resolved"] = mode  # `mode` do người viết giữ nguyên (thường là "auto") → đổi model sẽ chọn lại
        s["mode_reason"] = why
        if mode == "code":
            s["gen_sec"] = None
            s["start_frame"]["prompt"] = ""
            s["end_frame"]["prompt"] = ""
            s["video_prompt"] = ""
            continue
        s["gen_sec"] = gen_seconds(s, caps, mode=mode)
        s["start_frame"]["prompt"] = frame_prompt(sb, s, "start") if mode != "ingredients" else ""
        s["end_frame"]["prompt"] = frame_prompt(sb, s, "end") if mode == "frames_start_end" else ""
        s["video_prompt"] = video_prompt(sb, s, mode)
    for ing in sb.get("ingredients", []):
        ing["image_prompt"] = ingredient_prompt(sb, ing)
    for v in sb.get("thumbnail", {}).get("variants", []):
        v["bg_prompt"] = thumbnail_prompt(sb, v, "16:9")
        v["bg_prompt_vertical"] = thumbnail_prompt(sb, v, "9:16")
    sb.setdefault("outro", {})["bg_prompt"] = outro_prompt(sb)
    return sb


def word_count(text):
    return len(re.findall(r"[A-Za-z0-9#'’-]+", text or ""))
