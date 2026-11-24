"""Prompt + storyboard linter. Chạy tự động trước khi xuất scripts.html.

level: "error" (phải sửa — pipeline dừng) · "warn" (nên xem) · "info".
"""
import re

from . import compiler
from . import lang, tts
from .common import block, channel, spoken_syllables

TEXT_RISK = re.compile(
    r"(\"[^\"]{2,}\"|“[^”]{2,}”|(?<![A-Za-z])'[A-Za-z][^']{3,}'(?![A-Za-z])|\b(text|texts|caption|subtitle|subtitles|letters?|words?|"
    r"label(?:led|ed|s)?|sign(?:s|board)?|title|writing|written|reads?|logo|typography|font|digits?|numbers? on|"
    r"display(?:s|ing)? the number|scoreboard)\b|\d+\s?(°c|°f|km|kg|%|kcal|cal|m/s|km/h|mph|x)\b)",
    re.I)
NEGATION = re.compile(r"\b(no|not|don't|never|without)\s+\w+", re.I)
CROSS_REF = ("same as", "previous clip", "as before", "continue the previous", "like clip", "see above", "etc.")
BLOCK_KEYS = {"MOTION": "motion", "AUDIO": "audio"}
# Hành động cố ý trái với một mục AVOID → gợi ý avoid_drop
AVOID_CONFLICT = {
    "extra characters": re.compile(r"\b(crowd|line of|row of|group of|identical|clones?|two runners|many)\b", re.I),
    "morphing": re.compile(r"\b(swell|morph|transform|turns? into|grows? into|melts?)\b", re.I),
    "camera shake": re.compile(r"\b(shake the camera|camera shakes|earthquake)\b", re.I),
}


def _issue(level, where, msg):
    return {"level": level, "where": where, "msg": msg}


def _has_block(prompt, name):
    return block(name)[:48] in prompt


def lint_shot(sb, s, caps, img_caps):
    out = []
    tag = s["id"]
    mode = s.get("mode_resolved") or s.get("mode")
    if mode == "code":
        return out
    lim = channel().get("lint", {})
    vp = s.get("video_prompt", "")
    # 1. đủ 4 block
    for label, name in BLOCK_KEYS.items():
        if not _has_block(vp, name):
            out.append(_issue("error", tag, f"Prompt video thiếu block {label}."))
    if "Avoid:" not in vp:
        out.append(_issue("error", tag, "Prompt video thiếu block AVOID."))
    if "Background stays pure black and static" not in vp:
        out.append(_issue("error", tag, "Prompt video thiếu block STYLE."))
    # 2. giới hạn từ
    n = compiler.word_count(vp)
    scene_n = compiler.word_count(compiler.scene_part(vp))
    if n > lim.get("video_max_words", 170):
        out.append(_issue("error", tag, f"Prompt video {n} từ > giới hạn {lim.get('video_max_words', 170)}."))
    if scene_n > lim.get("scene_max_words", 70):
        out.append(_issue("warn", tag, f"Phần mô tả cảnh {scene_n} từ — nên ≤ {lim.get('scene_max_words', 70)} "
                                       f"(chia bớt sang shot khác)."))
    if scene_n < lim.get("scene_min_words", 10):
        out.append(_issue("warn", tag, f"Phần mô tả cảnh chỉ {scene_n} từ — hành động quá mơ hồ."))
    # 3. ràng buộc frame
    if mode in ("frames_start", "frames_start_end") and "provided start frame" not in vp:
        out.append(_issue("error", tag, "Mode Frames nhưng prompt không nói rõ start frame."))
    if mode == "frames_start_end" and "provided end frame" not in vp:
        out.append(_issue("error", tag, "Mode Start+End nhưng prompt không nói rõ end frame."))
    if mode == "frames_start_end" and not s.get("end_frame", {}).get("desc"):
        out.append(_issue("error", tag, "Mode Start+End nhưng thiếu end_frame.desc."))
    if mode in ("frames_start", "frames_start_end") and not (s["start_frame"].get("desc") or
                                                              s["start_frame"].get("seed_from")):
        out.append(_issue("error", tag, "Thiếu start_frame.desc."))
    # 4. chữ cần hiển thị không được nằm trong mô tả hình
    acts = " ".join(a if isinstance(a, str) else a.get("do", "") for a in s.get("action") or [])
    authored = " ".join([acts, s.get("start_frame", {}).get("desc", ""),
                         s.get("end_frame", {}).get("desc", ""), s.get("camera", "")])
    m = TEXT_RISK.search(authored)
    if m:
        out.append(_issue("error", tag, f"Mô tả hình có chữ/số cần hiển thị ('{m.group(0).strip()}'). Chữ luôn thêm "
                                        f"ở hậu kỳ qua 'onscreen' — thay bằng hình/biểu tượng."))
    neg = sorted({x.lower() for x in NEGATION.findall(authored)})
    if neg:
        out.append(_issue("warn", tag, f"Mô tả có cách viết phủ định ({', '.join(neg[:3])}) — viết điều MUỐN thấy; "
                                       f"block Avoid đã là lưới an toàn."))
    dropped = {d.lower() for d in s.get("avoid_drop") or []}
    for item, rx in AVOID_CONFLICT.items():
        if item not in dropped and rx.search(acts + " " + s.get("start_frame", {}).get("desc", "")):
            out.append(_issue("warn", tag, f"Hành động có vẻ trái với Avoid '{item}' — thêm \"avoid_drop\": [\"{item}\"] "
                                           f"nếu đó là chủ ý."))
    low = authored.lower()
    for b in CROSS_REF:
        if b in low:
            out.append(_issue("error", tag, f"Có cụm tham chiếu chéo '{b}' — mỗi prompt phải tự đủ nghĩa."))
    # 5. gen_sec hợp lệ với model
    durs = compiler.allowed_durations(caps, mode)
    g = s.get("gen_sec")
    speed = float(s.get("trim", {}).get("speed") or 1.0)
    if durs and g not in durs:
        out.append(_issue("error", tag, f"gen_sec={g} không hợp lệ với model (cho phép: {durs})."))
    if g and g < s["target_sec"] * speed + channel()["flow"]["gen_margin_sec"] - 1e-6:
        out.append(_issue("warn", tag, f"gen_sec {g}s < target {s['target_sec']}s×{speed:g} + "
                                       f"{channel()['flow']['gen_margin_sec']}s — ít đất để auto-trim."))
    # 6. mode & ingredients
    if mode == "ingredients":
        mx = caps.get("ingredients_max") or 0
        if len(s.get("refs") or []) > mx:
            out.append(_issue("error", tag, f"{len(s['refs'])} ingredients > tối đa {mx} của model."))
    if len(s.get("refs") or []) > (img_caps.get("max_refs") or 1):
        out.append(_issue("error", tag, f"{len(s['refs'])} ảnh ref > tối đa {img_caps.get('max_refs')} của image model."))
    if s.get("mode") not in ("auto", mode):
        out.append(_issue("warn", tag, f"Mode '{s.get('mode')}' không dùng được → {mode}. {s.get('mode_reason', '')}"))
    if speed > channel()["pacing"]["speed_ramp_max"] + 1e-6:
        out.append(_issue("warn", tag, f"speed {speed:g} > {channel()['pacing']['speed_ramp_max']} — dễ giật."))
    return out


def lint_pacing(sb):
    out = []
    p = channel()["pacing"]
    d = channel()["duration"]
    shots = sb["shots"]
    if not shots:
        return [_issue("error", "storyboard", "Chưa có shot nào.")]
    if shots[0]["target_sec"] > p["hook_max_sec"] + 1e-6:
        out.append(_issue("warn", shots[0]["id"], f"Hook dài {shots[0]['target_sec']}s > {p['hook_max_sec']}s."))
    durs = [s["target_sec"] for s in shots]
    avg = sum(durs) / len(durs)
    if not p["shot_avg_min"] - 1e-6 <= avg <= p["shot_avg_max"] + 1e-6:
        out.append(_issue("warn", "nhịp", f"Shot trung bình {avg:.2f}s — mục tiêu {p['shot_avg_min']}–"
                                         f"{p['shot_avg_max']}s."))
    for s in shots:
        mx = p.get("code_shot_max_sec", 5.0) if s.get("mode_resolved") == "code" else p["shot_max_sec"]
        if s["target_sec"] > mx + 1e-6:  # shot code có chuyển động liên tục bên trong (camera + đạo cụ) → được dài hơn
            out.append(_issue("error", s["id"], f"Shot dài {s['target_sec']}s > tối đa {mx}s."))
    total = sum(durs)
    if not d["min_sec"] <= total <= d["max_sec"]:
        out.append(_issue("warn", "nhịp", f"Tổng {total:.1f}s ngoài khoảng {d['min_sec']}–{d['max_sec']}s "
                                         f"(chưa tính outro)."))
    out += lint_script(sb)
    if shots[0].get("beat") != "hook":
        out.append(_issue("warn", shots[0]["id"], "Shot đầu nên là beat 'hook'."))
    beats = {s.get("beat") for s in shots}
    for b in ("payoff",):
        if b not in beats:
            out.append(_issue("warn", "kịch bản", f"Thiếu beat '{b}'."))
    from . import codeshot  # noqa: PLC0415
    st = sb.get("style_resolved") or sb.get("style") or "forward"
    html_scenes = [
        (s.get("code") or {}).get("scene") for s in shots
        if (s.get("mode_resolved") or s.get("mode")) == "code" and codeshot.engine_of(s, st) == "html"
    ]
    if len(html_scenes) >= 5 and "scene" not in html_scenes:
        out.append(_issue("warn", "kịch bản",
                          "Mọi shot html đều dùng beat mẫu (chưa có 'scene' dàn cảnh tự do) — nên đổi 1–2 khoảnh khắc "
                          "hành động sang beat 'scene' để video không giống đổi icon trên cùng một khung."))
    return out


CONTRACTABLE = re.compile(r"\b(it is|do not|does not|is not|are not|can not|cannot|will not|that is|there is|"
                          r"you are|they are|we are|did not|would not|could not|should not|has not|have not)\b", re.I)


def lint_script(sb):
    """Quy tắc viết script (cartoon-short-kit, kênh tiếng Anh): ~3.7 từ/giây, câu 8–15 từ, dạng rút gọn, số viết bằng
    chữ, câu đầu là hook nghịch lý nói như sự thật, không tả lại hình. Mật độ tính theo từ ĐỌC (số đã đổi sang chữ)."""
    out = []
    shots = sb["shots"]
    d = channel()["duration"]
    sc = channel().get("script", {})
    if not lang.language().startswith("en"):  # kênh tiếng Việt cũ: đếm âm tiết như trước
        return _lint_vo_density_vi(sb)
    wps, lo, hi = lang.pace(), sc.get("words_per_sec_min", 3.0), sc.get("words_per_sec_max", 4.3)
    smin, smax = sc.get("sentence_words", [8, 15])
    hard = sc.get("sentence_words_hard_max", 20)
    total_words = 0
    i = 0
    while i < len(shots):
        vo = tts.strip_tags(shots[i].get("vo", ""))
        if not vo:
            i += 1
            continue
        j = i + 1
        while j < len(shots) and not tts.strip_tags(shots[j].get("vo", "")):
            j += 1
        span = sum(s["target_sec"] for s in shots[i:j])
        n = lang.word_count(vo)
        total_words += n
        rate = n / max(span, 0.1)
        tag = shots[i]["id"]
        if rate > hi:
            out.append(_issue("warn", tag, f"Lời dày {rate:.1f} từ/giây trên {span:.1f}s hình (nên ≈ {wps}, ≤ {hi})."))
        elif rate < lo:
            out.append(_issue("warn", tag, f"Lời thưa {rate:.1f} từ/giây trên {span:.1f}s hình — VO sẽ co các shot lại."))
        if re.search(r"\d", vo):
            out.append(_issue("warn", tag, "Số trong lời đọc nên viết bằng chữ (\"one thousand\", không \"1,000\"): "
                              + vo[:60]))
        for sent in [x.strip() for x in re.split(r"(?<=[.!?])\s+", vo) if x.strip()]:
            k = lang.word_count(sent)
            if k > hard:
                out.append(_issue("warn", tag, f"Câu dài {k} từ (> {hard}) — tách đôi: {sent[:60]}"))
            elif k > smax and k > 3:
                out.append(_issue("info", tag, f"Câu {k} từ (nên {smin}–{smax}): {sent[:60]}"))
        m = CONTRACTABLE.search(vo)
        if m:
            out.append(_issue("info", tag, f"Văn nói nên rút gọn: '{m.group(0)}' → dạng it's / don't / isn't…"))
        if re.search(r"\b(as you can see|here we see|in this shot|on screen|you can see)\b", vo, re.I):
            out.append(_issue("warn", tag, "Đừng tả lại cái người xem đang thấy."))
        i = j
    if total_words:
        est = total_words / wps
        if est < d["min_sec"] - 3:
            out.append(_issue("warn", "nhịp", f"Lời {total_words} từ ≈ {est:.0f}s ở {wps} từ/giây — "
                                             f"ngắn hơn {d['min_sec']}s "
                                             f"(20s ≈ 75 từ, 30s ≈ 110, 45s ≈ 165)."))
        elif est > d["max_sec"] + 2:
            out.append(_issue("warn", "nhịp", f"Lời {total_words} từ ≈ {est:.0f}s — dài hơn {d['max_sec']}s."))
    first = next((tts.strip_tags(s.get("vo", "")) for s in shots if tts.strip_tags(s.get("vo", ""))), "")
    if first.rstrip().endswith("?"):
        out.append(_issue("info", shots[0]["id"], "Hook nên là một nghịch lý NÓI NHƯ SỰ THẬT, không phải câu hỏi."))
    beats = [s.get("beat") for s in shots]
    if "twist" not in beats:
        out.append(_issue("warn", "kịch bản", "Thiếu beat 'twist' — video phải kết bằng twist."))
    return out


def _lint_vo_density_vi(sb):
    out = []
    shots = sb["shots"]
    i = 0
    while i < len(shots):
        if not shots[i].get("vo"):
            i += 1
            continue
        j = i + 1
        while j < len(shots) and not shots[j].get("vo"):
            j += 1
        span = sum(s["target_sec"] for s in shots[i:j])
        rate = spoken_syllables(shots[i]["vo"]) / max(span, 0.1)
        if rate > 6.2:
            out.append(_issue("warn", shots[i]["id"], f"Lời đọc dày {rate:.1f} âm tiết/giây trên {span:.1f}s hình."))
        i = j
    return out


def lint_meta(sb):
    out = []
    mx = channel()["thumbnail"]["max_words"]
    vs = sb.get("thumbnail", {}).get("variants", [])
    if not 3 <= len(vs) <= 5:
        out.append(_issue("warn", "thumbnail", f"Có {len(vs)} biến thể — nên 3–5."))
    title_words = {w.lower() for w in re.findall(r"\w+", sb.get("title", ""))}
    for v in vs:
        tw = re.findall(r"\w+(?:['’]\w+)?", v.get("text", ""))  # "WON'T" là một từ
        if len(tw) > mx:
            out.append(_issue("warn", v["id"], f"Chữ thumbnail '{v['text']}' có {len(tw)} từ > {mx}."))
        if tw and sum(w.lower() in title_words for w in tw) / len(tw) > 0.6:
            out.append(_issue("warn", v["id"], "Chữ thumbnail lặp lại tiêu đề — nên bổ sung, không lặp."))
    if sb.get("outro", {}).get("enabled") and not sb.get("outro", {}).get("teaser"):
        out.append(_issue("warn", "outro", "Chưa có outro.teaser (câu hỏi thí nghiệm tiếp theo)."))
    from . import userassets  # noqa: PLC0415 — tài sản người dùng (SVG/Lottie/Rive) phải có ghi chú nguồn/giấy phép
    for s in sb.get("shots", []):
        for kind, name, note in userassets.license_notes((s.get("code") or {}).get("params") or {}):
            if not note:
                out.append(_issue("warn", s.get("id", "?"), f"{kind} '{name}' chưa ghi nguồn/giấy phép — dùng thương mại "
                                  "cần chắc quyền (SVG: --license khi nhập; Lottie/Rive: file <tên>.license.txt)."))
    return out


def lint_clutter(sb):
    """Clutter Linter (Vòng 12 — Less Is More): giới hạn mật độ vật thể & chữ on-screen mỗi shot."""
    out = []
    for s in sb.get("shots") or []:
        sid = s.get("id", "?")
        code = s.get("code") or {}
        scene = code.get("scene")
        params = code.get("params") or {}
        if scene == "scene":
            prominent = [a for a in (params.get("actors") or []) if float(a.get("z") or 0) < 1.8]
            if len(prominent) > 4:
                out.append(_issue(
                    "warn", sid,
                    f"Cảnh 2D 'scene' có {len(prominent)} actor nổi bật (> 4) — Less Is More: giữ ≤ 3 (1 Hero + 1 cơ chế).",
                ))
        elif scene == "stage":
            prominent = [p for p in (params.get("props") or []) if p.get("frame") is not False]
            if len(prominent) > 5:
                out.append(_issue(
                    "warn", sid,
                    f"Cảnh 3D 'stage' có {len(prominent)} prop trong khung (> 5) — nên tinh gọn ≤ 4 để tránh rối mắt.",
                ))
        if scene not in ("fact", "title") and s.get("beat") != "outro":
            clusters = []
            for k in ("kicker", "title", "sub", "result"):
                if params.get(k):
                    clusters.append(str(params[k]))
            for lb in params.get("labels") or []:
                if isinstance(lb, dict) and lb.get("text"):
                    clusters.append(str(lb["text"]))
            for ov in params.get("overlay2d") or []:
                if isinstance(ov, dict) and ov.get("text"):
                    clusters.append(str(ov["text"]))
            for tf in s.get("text_fx") or []:
                if isinstance(tf, dict) and tf.get("text"):
                    clusters.append(str(tf["text"]))
            words = sum(len(re.findall(r"\S+", c)) for c in clusters)
            if len(clusters) > 3 or words > 12:
                out.append(_issue(
                    "warn", sid,
                    f"Quá nhiều chữ on-screen ({len(clusters)} cụm, {words} từ; chuẩn ≤ 3 cụm & ≤ 12 từ) — "
                    "ưu tiên kể chuyện bằng hình ảnh, không lặp lại lời thoại.",
                ))
    return out


def lint(sb):
    """sb phải là bản đã compile (compiler.compile_all)."""
    name, caps = compiler.video_caps(sb)
    _, img = compiler.image_caps(sb)
    out = []
    if caps.get("status") == "deprecated":
        out.append(_issue("warn", "model", f"{name} sẽ bị gỡ khỏi Flow ngày {caps.get('removal_date')} — "
                                           f"nên dùng {compiler.flow_models()['default_video_model']}."))
    for s in sb["shots"]:
        out += lint_shot(sb, s, caps, img)
    out += lint_pacing(sb)
    out += lint_meta(sb)
    out += lint_clutter(sb)
    out += lint_motion(sb)
    return out


def lint_motion(sb):
    """Khuôn motion lặp (vòng 10, vidlib/motionplan): tỉ lệ thẻ chung chung, số shot cơ chế, giống khung xương video
    trước, verb/mechanism sai tên. Cảnh báo kèm gợi ý cơ chế; chỉ thành lỗi khi channel.json → motion.block = true.
    Dự án sinh trước motion.apply_since không bị soi (video đã đăng)."""
    from . import motionplan  # noqa: PLC0415
    if motionplan.legacy(sb.get("slug")):
        return []
    try:
        return motionplan.lint(sb, _issue)
    except Exception as ex:  # noqa: BLE001 — lint motion không được làm hỏng bước prompts
        return [_issue("info", "motion", f"không chấm được khuôn motion: {ex}")]


def errors(issues):
    return [i for i in issues if i["level"] == "error"]


def format_issues(issues):
    icon = {"error": "✖", "warn": "⚠", "info": "·"}
    return "\n".join(f"  {icon[i['level']]} [{i['where']}] {i['msg']}" for i in issues)
