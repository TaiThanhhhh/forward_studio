"""Agency Viral & Craft Scorecard (Vòng 13–14 — 0..100 trên 6 trục, Format-Agnostic).

Chấm điểm tự động mức độ điện ảnh, nhịp giữ chân và tính chống lặp "PowerPoint" của một storyboard
theo đúng Format Family của video (`evidence_board_doc`, `cinema_3d_film`, `editorial_infographic`,
`infinite_zoom_journey`, `fast_tech_autopsy`) để KHÔNG ép mọi video phải dùng chung 1 bộ widget:
- hook_loop (0..20): Hook ≤ 2.4s, cold-open giàu hình ảnh, không mở bài kiểu bài giảng, kết vòng lặp/pull-back.
- narrative_freshness (0..15): có Director Archetype / Format Family hợp lệ, mạch But/Therefore, re-hook giữa video.
- visual_craft (0..25): chiều sâu & mật độ thủ công đúng chuẩn Format Family, phạt chuỗi thẻ phẳng/lặp khuôn.
- camera_matchcut (0..15): đa dạng góc máy 3D/2D hoặc biên đạo cú máy 1-shot bảng đen + chuyển cảnh/liên kết chủ đích.
- audio_tension (0..15): hook impact / mood khớp archetype, riser hoặc SFX đa dạng ≥ 50% shot, cú ngắt twist/payoff.
- retention_pacing (0..10): shot TB 2.2–4.0s, nhịp lời 2.4–3.6 wps, 0 lỗi clutter Vòng 12.
"""
import re

from . import codeshot, lang, linter, narratives, tts
from .common import channel

MAX_AXES = {
    "hook_loop": 20,
    "narrative_freshness": 15,
    "visual_craft": 25,
    "camera_matchcut": 15,
    "audio_tension": 15,
    "retention_pacing": 10,
}

AXIS_LABELS = {
    "hook_loop": "Hook & Seamless Loop",
    "narrative_freshness": "Độ tươi kể chuyện (But/Therefore & Re-Hook)",
    "visual_craft": "Mỹ thuật & Chiều sâu (Format-Agnostic)",
    "camera_matchcut": "Góc máy / Biên đạo Camera & Match Cut",
    "audio_tension": "Đường cong âm thanh & SFX",
    "retention_pacing": "Nhịp giữ chân & Visual Budget",
}

COLD_OPEN_SCENES = frozenset({
    "drop", "stage", "scene", "xray_cutaway", "dossier", "hero_stat", "code_terminal", "chat_prompt",
})
BOARD_HOOK_RECIPES = frozenset({
    "number_card", "reveal_photo", "doc_focus", "counter", "stamp", "title_glitch", "silent_film",
})
BOARD_RICH_RECIPES = frozenset({
    "reveal_photo", "doc_focus", "counter", "thesis", "network_reveal", "silent_film", "stamp", "number_card",
})
BOARD_REHOOK_RECIPES = frozenset({"stamp", "connect", "counter", "reveal_photo", "thesis", "silent_film"})
TECH_RICH_SCENES = frozenset({
    "process", "split", "xray_cutaway", "dossier", "hero_stat", "stage", "code_terminal", "chat_prompt",
})
ZOOM_RICH_SCENES = frozenset({"scale", "timeline", "xray_cutaway", "stage"})
RICH_SCENES = frozenset({"dossier", "xray_cutaway", "hero_stat", "stage", "code_terminal", "chat_prompt"})
FLAT_CARDS = frozenset({"title", "fact", "counter", "compare"})
PURPOSEFUL_TRANSITIONS = frozenset({"iris_match", "whip_match", "tape_stop", "match", "whip"})
AGENCY_TRANSITIONS = frozenset({"iris_match", "whip_match", "tape_stop"})
HOOK_IMPACT_SFX = frozenset({
    "sub_drop", "boom", "hit", "impact", "sting", "thud", "whoosh", "swish_match", "tape_stop",
    "stamp", "pin", "shutter", "slam", "crash",
})
ESCALATION_SFX = frozenset({
    "riser", "riser_long", "heartbeat", "neural_pulse", "paper_rustle", "tick",
    "marker", "paper", "string", "tape", "shutter", "pin",
})
CONTRAST_SFX = frozenset({
    "hit", "sting", "sting_low", "boom", "sub_drop", "tape_stop", "riser_long", "stamp", "crash",
})

LECTURE_HOOK_RX = re.compile(
    r"\b(today we|did you know|let'?s talk about|in this video|welcome to|have you ever wondered)\b",
    re.I,
)
CAUSAL_RX = re.compile(
    r"\b(but|yet|instead|until|except|because|so|forces|triggers|however|actually|never|zero)\b",
    re.I,
)
CONTRAST_RX = re.compile(r"\b(but|yet|instead|until|except|however|actually)\b", re.I)


def grade_of(total):
    if total >= 90:
        return "S"
    if total >= 80:
        return "A"
    if total >= 70:
        return "B"
    if total >= 60:
        return "C"
    return "D"


def _shot_engine_scene(sb, sh):
    style = sb.get("style_resolved") or sb.get("style") or "forward"
    code = sh.get("code") or {}
    scene = code.get("scene")
    mode = sh.get("mode_resolved") or sh.get("mode")
    if code.get("engine") == "board":
        return "board", str(sh.get("beat_recipe") or "board").lower()
    if scene:
        eng = code.get("engine")
        if not eng:
            try:
                eng = codeshot.engine_of(sh, style)
            except Exception:  # noqa: BLE001
                eng = "three" if scene == "stage" else "html"
        return eng or "html", str(scene)
    if mode != "code":
        return "flow", "flow"
    return "html", ""


def _board_recipe(sh):
    r = (sh.get("beat_recipe") or "").strip().lower()
    if r:
        return r
    b = sh.get("board") or {}
    if b.get("old") and b.get("new"):
        return "thesis"
    if b.get("film"):
        return "silent_film"
    if b.get("number"):
        return "number_card"
    if b.get("lines"):
        return "doc_focus"
    if b.get("counter") or (b.get("to") is not None and b.get("unit")):
        return "counter"
    if sh.get("beat") == "outro" and not (sh.get("code") or {}).get("scene"):
        return "network_reveal"
    return "reveal_photo"


def detect_format(sb, eng_scenes):
    """Nhận diện Format Family của storyboard để chấm điểm công bằng theo đúng ngôn ngữ hình ảnh."""
    valid = set(narratives.format_ids())
    explicit = sb.get("format_family_resolved") or sb.get("format_family")
    if explicit in valid:
        return explicit

    asm = sb.get("assembly_resolved") or sb.get("assembly") or ""
    style = str(sb.get("style_resolved") or sb.get("style") or "").lower()
    shots = list(sb.get("shots") or [])
    n = max(1, len(shots))
    board_n = sum(1 for sh, (eng, _) in zip(shots, eng_scenes) if eng == "board" or sh.get("beat_recipe"))
    if asm == "board_spine" or style.startswith("board") or board_n / n >= 0.50:
        return "evidence_board_doc"

    stage_n = sum(1 for eng, sc in eng_scenes if eng == "three" and sc == "stage")
    if len(shots) >= 3 and stage_n / n >= 0.80:
        return "cinema_3d_film"

    scale_n = sum(1 for _, sc in eng_scenes if sc == "scale")
    if style == "scale-zoom-black" or scale_n >= 2:
        return "infinite_zoom_journey"

    return "editorial_infographic"


def _shot_sfx(sh):
    out = []
    for x in sh.get("sfx") or []:
        name = x if isinstance(x, str) else (x.get("name") or x.get("sfx") or "")
        if name:
            out.append(str(name).split(":")[0].strip().lower())
    params = (sh.get("code") or {}).get("params") or {}
    if isinstance(params.get("sfx"), str) and params["sfx"].strip():
        out.append(params["sfx"].split(":")[0].strip().lower())
    for c in params.get("cues") or []:
        if isinstance(c, dict):
            name = c.get("sfx") or c.get("name") or ""
            if name:
                out.append(str(name).split(":")[0].strip().lower())
    return out


def _has_explicit_loop(sb, shots):
    outro = sb.get("outro") or {}
    if outro.get("mode") == "loop":
        return True
    if outro.get("loop_bridge") or sb.get("loop_bridge"):
        return True
    if shots and (shots[-1].get("loop_bridge") or shots[-1].get("transition_out") == "loop"):
        return True
    return False


def _score_hook_loop(sb, shots, eng_scenes, fmt, suggestions):
    pts = 0
    s0 = shots[0]
    eng0, sc0 = eng_scenes[0]
    dur0 = float(s0.get("target_sec") or 0)
    if 0 < dur0 <= 2.4:
        pts += 6
    elif 0 < dur0 <= 2.8:
        pts += 2
        suggestions.append(f"Rút ngắn hook {s0.get('id', 'C01')} ({dur0:.1f}s → ≤ 2.4s) để tăng giữ chân 3 giây đầu.")
    else:
        suggestions.append(f"Hook {s0.get('id', 'C01')} dài {dur0:.1f}s (> 2.4s) — cắt gọn vào thẳng nghịch lý ở frame 0.")

    if fmt == "evidence_board_doc":
        rec0 = _board_recipe(s0)
        cold_ok = eng0 in ("board", "three", "flow") or rec0 in BOARD_HOOK_RECIPES or sc0 in COLD_OPEN_SCENES
    elif fmt == "infinite_zoom_journey":
        cold_ok = sc0 in COLD_OPEN_SCENES or sc0 in ("scale", "timeline") or eng0 == "flow"
    else:
        cold_ok = sc0 in COLD_OPEN_SCENES or eng0 == "flow"

    if cold_ok:
        pts += 6
    else:
        suggestions.append(
            "Mở đầu bằng cảnh hành động/cận cảnh (`stage`, `xray_cutaway`, `dossier`, `hero_stat`, "
            f"`scene`, `drop` hoặc Flow) thay vì thẻ `{sc0 or 'tĩnh'}`."
        )

    vo0 = tts.strip_tags(s0.get("vo", "")).strip()
    if vo0 and not LECTURE_HOOK_RX.search(vo0):
        pts += 4
    elif not vo0:
        pts += 2
    else:
        suggestions.append("Bỏ lời mở bài giáo khoa ('Today we...', 'Did you know...') — vào thẳng nghịch lý ở câu 1.")

    has_board_payoff = fmt == "evidence_board_doc" and any(_board_recipe(s) == "network_reveal" for s in shots[-2:])
    if _has_explicit_loop(sb, shots) or has_board_payoff:
        pts += 4
    else:
        suggestions.append("Dùng `outro.mode: \"loop\"` (hoặc câu cầu nối vòng lặp) để đẩy AVD > 100%.")
    return max(0, min(MAX_AXES["hook_loop"], pts))


def _score_narrative(sb, shots, eng_scenes, fmt, history, suggestions):
    pts = 0
    valid_archs = set(narratives.archetype_ids())
    valid_fmts = set(narratives.format_ids())
    arch = sb.get("archetype_resolved") or sb.get("archetype")
    explicit_fmt = sb.get("format_family_resolved") or sb.get("format_family")
    if arch in valid_archs or explicit_fmt in valid_fmts:
        pts += 4
    else:
        suggestions.append(
            "Khai báo `archetype` (6 Director Archetypes) hoặc `format_family` (5 Format Families) hợp lệ."
        )

    causal_shots = sum(1 for s in shots if CAUSAL_RX.search(tts.strip_tags(s.get("vo", ""))))
    if causal_shots >= 3:
        pts += 6
    elif causal_shots == 2:
        pts += 4
        suggestions.append("Tăng mạch nhân-quả But/Therefore (hiện chỉ 2 shot có từ nối tương phản/nhân-quả, mục tiêu ≥ 3).")
    elif causal_shots == 1:
        pts += 2
        suggestions.append("Kịch bản còn tuyến tính ('and then') — thêm lực bẻ lái But/Therefore ở ≥ 3 shot.")
    else:
        suggestions.append(
            "Thiếu từ nối nhân-quả/tương phản (`but`, `yet`, `instead`, `because`, `forces`...) — "
            "viết lại theo luật But/Therefore."
        )

    n = len(shots)
    has_rehook = False
    if n >= 3:
        lo = max(1, n // 4)
        hi = min(n - 1, max(lo, (3 * n) // 4))
        for i in range(lo, hi + 1):
            if i >= n:
                break
            eng_switch = eng_scenes[i][0] != eng_scenes[i - 1][0]
            trans_interrupt = shots[i].get("transition_in") in AGENCY_TRANSITIONS
            vo_contrast = bool(CONTRAST_RX.search(tts.strip_tags(shots[i].get("vo", ""))))
            board_shift = (
                fmt == "evidence_board_doc"
                and (_board_recipe(shots[i]) in BOARD_REHOOK_RECIPES
                     or bool((shots[i].get("board") or {}).get("from")))
            )
            cam_shift = False
            if fmt == "cinema_3d_film":
                p_cur = (((shots[i].get("code") or {}).get("params") or {}).get("frame") or {}).get("preset")
                p_prev = (((shots[i - 1].get("code") or {}).get("params") or {}).get("frame") or {}).get("preset")
                cam_shift = bool(p_cur and p_prev and p_cur != p_prev)
            if eng_switch or trans_interrupt or vo_contrast or board_shift or cam_shift:
                has_rehook = True
                break
    if has_rehook:
        pts += 5
    else:
        suggestions.append(
            "Thêm Mid-Video Re-Hook ở nửa giữa video (đổi engine, dùng "
            "`iris_match`/`tape_stop`/`whip_match`, hoặc bẻ lái bằng từ nối tương phản)."
        )

    if history and isinstance(history, list):
        recent_archs = [
            h.get("archetype_resolved") or h.get("archetype")
            for h in history[:2]
            if isinstance(h, dict)
        ]
        recent_fmts = [
            h.get("format_family_resolved") or h.get("format_family")
            for h in history[:1]
            if isinstance(h, dict)
        ]
        if arch and arch in recent_archs:
            pts = max(0, pts - 2)
            suggestions.append(f"Archetype `{arch}` trùng video gần nhất — xoay sang phong cách đạo diễn khác.")
        elif explicit_fmt and explicit_fmt in recent_fmts:
            pts = max(0, pts - 2)
            suggestions.append(f"Format Family `{explicit_fmt}` trùng video ngay trước — xoay sang định dạng khác.")

    return max(0, min(MAX_AXES["narrative_freshness"], pts))


def _score_visual_craft(sb, shots, eng_scenes, fmt, suggestions):
    n = max(1, len(shots))

    if fmt == "evidence_board_doc":
        recipes = [_board_recipe(s) for s in shots]
        rich_count = 0
        for sh, (eng, _), rec in zip(shots, eng_scenes, recipes):
            b = sh.get("board") or {}
            if rec in BOARD_RICH_RECIPES or eng in ("three", "flow") or b.get("circle") or b.get("from"):
                rich_count += 1
        rich_share = rich_count / n
        rich_pts = round(14 * min(1.0, rich_share / 0.50))
        if rich_share < 0.50:
            suggestions.append(
                f"Bảng đen mới có {rich_share:.0%} thẻ chứng cứ giàu chiều sâu — bổ sung `REVEAL_PHOTO`, "
                "`DOC_FOCUS` khoanh đỏ, `COUNTER`, `STAMP`, `THESIS`."
            )

        tactile_links = sum(
            1 for sh, rec in zip(shots, recipes)
            if rec in ("connect", "stamp", "name_tag", "thesis")
            or bool((sh.get("board") or {}).get("from"))
            or bool((sh.get("board") or {}).get("circle"))
            or bool((sh.get("board") or {}).get("marks"))
        )
        tactile_pts = 4 if tactile_links >= 2 else (2 if tactile_links == 1 else 0)
        if tactile_links < 2:
            suggestions.append(
                "Thêm ≥ 2 dấu vết điều tra trên bảng đen (khoanh tròn `board.circle`, chỉ đỏ `CONNECT`/`board.from`, "
                "`STAMP` hoặc `NAME_TAG`)."
            )

        unique_rec = len(set(recipes))
        div_pts = round(7 * min(1.0, unique_rec / 5.0))
        if unique_rec < 5:
            suggestions.append(f"Mới dùng {unique_rec} loại beat bảng đen (mục tiêu ≥ 5) — đa dạng hoá thẻ chứng cứ.")

        max_same_run, cur_run, prev_r = 0, 0, None
        for r in recipes:
            if r == prev_r and r != "reveal_photo":
                cur_run += 1
            else:
                cur_run = 1
                prev_r = r
            max_same_run = max(max_same_run, cur_run)
        penalty = min(8, (max_same_run - 2) * 3) if max_same_run > 2 else 0
        if penalty:
            suggestions.append(f"Lặp {max_same_run} thẻ `{prev_r}` liên tiếp trên bảng đen — xen loại chứng cứ khác.")
        return max(0, min(MAX_AXES["visual_craft"], rich_pts + tactile_pts + div_pts - penalty))

    if fmt == "cinema_3d_film":
        rich_count = 0
        dynamic_count = 0
        setups = set()
        for sh, (eng, sc) in zip(shots, eng_scenes):
            params = (sh.get("code") or {}).get("params") or {}
            if eng == "three" and sc == "stage":
                has_actors = bool(params.get("actors") or params.get("props") or params.get("hero")
                                  or params.get("subject") or params.get("creatures"))
                rich_count += 1 if has_actors or params else 0
                if params.get("fx") or params.get("physics") or params.get("camera") or params.get("lights"):
                    dynamic_count += 1
                pr = (params.get("frame") or {}).get("preset") or "default"
                bg = str(params.get("env") or params.get("mood") or params.get("fx") or "")
                setups.add(f"{pr}:{bg[:16]}")
            elif eng == "flow":
                rich_count += 1
                dynamic_count += 1
                setups.add("flow")
        rich_share = rich_count / n
        rich_pts = round(14 * min(1.0, rich_share / 0.80))
        has_hud = bool(isinstance(sb.get("story_hud"), dict) and sb["story_hud"])
        depth_pts = 4 if (has_hud or dynamic_count / n >= 0.40) else 2
        div_pts = round(7 * min(1.0, len(setups) / 4.0))
        if len(setups) < 4:
            suggestions.append("Đa dạng hoá thêm góc máy, ánh sáng và bối cảnh 3D (mục tiêu ≥ 4 bố cục khác nhau).")
        return max(0, min(MAX_AXES["visual_craft"], rich_pts + depth_pts + div_pts))

    # editorial_infographic / infinite_zoom_journey / fast_tech_autopsy
    extra_rich = (
        ZOOM_RICH_SCENES if fmt == "infinite_zoom_journey"
        else TECH_RICH_SCENES if fmt == "fast_tech_autopsy"
        else RICH_SCENES
    )
    rich_count = 0
    for sh, (eng, sc) in zip(shots, eng_scenes):
        params = (sh.get("code") or {}).get("params") or {}
        if sc in RICH_SCENES or sc in extra_rich or eng == "flow":
            rich_count += 1
        elif sc == "scene" and len(params.get("actors") or []) >= 2:
            rich_count += 1
    rich_share = rich_count / n
    rich_pts = round(14 * min(1.0, rich_share / 0.40))
    if rich_share < 0.40:
        suggestions.append(
            f"Tỉ lệ shot giàu chiều sâu mới đạt {rich_share:.0%} (< 40%) — thêm `dossier`, "
            "`xray_cutaway`, `hero_stat`, 3D `stage` hoặc `scene` đa nhân vật."
        )

    has_hud = bool(isinstance(sb.get("story_hud"), dict) and sb["story_hud"]) or any(
        bool(s.get("story_hud")) or bool(((s.get("code") or {}).get("params") or {}).get("story_hud"))
        for s in shots
    )
    if fmt == "infinite_zoom_journey" and not has_hud:
        has_hud = any(sc == "scale" for _, sc in eng_scenes)
    hud_pts = 4 if has_hud else 0

    unique_scenes = len({sc for _, sc in eng_scenes if sc})
    target_div = 4.0 if fmt == "infinite_zoom_journey" else 5.0
    div_pts = round(7 * min(1.0, unique_scenes / target_div))
    if unique_scenes < int(target_div):
        suggestions.append(
            f"Mới dùng {unique_scenes} loại beat/cảnh khác nhau (mục tiêu ≥ {int(target_div)}) — đa dạng hoá nhịp hình."
        )

    max_flat_run, cur_run = 0, 0
    for _, sc in eng_scenes:
        if sc in FLAT_CARDS:
            cur_run += 1
            max_flat_run = max(max_flat_run, cur_run)
        else:
            cur_run = 0
    max_allowed = int((channel().get("viral") or {}).get("max_consecutive_flat_cards", 2))
    penalty = 0
    if max_flat_run > max_allowed:
        penalty = min(10, (max_flat_run - max_allowed) * 3 + 2)
        suggestions.append(
            f"Có {max_flat_run} thẻ phẳng liên tiếp (`title`/`fact`/`counter`/`compare`, chuẩn ≤ "
            f"{max_allowed}) — xen cảnh `xray_cutaway`, `dossier`, `stage` hoặc `scene`."
        )

    return max(0, min(MAX_AXES["visual_craft"], rich_pts + hud_pts + div_pts - penalty))


def _score_camera_matchcut(sb, shots, eng_scenes, fmt, suggestions):
    if fmt == "evidence_board_doc":
        recipes = [_board_recipe(s) for s in shots]
        has_pullback = "network_reveal" in recipes
        has_embedded_media = any(
            eng in ("three", "flow") or bool((s.get("board") or {}).get("fill"))
            for s, (eng, _) in zip(shots, eng_scenes)
        )
        synced_reveals = sum(1 for s in shots if bool((s.get("board") or {}).get("sync")))
        if has_pullback and (has_embedded_media or synced_reveals >= 2):
            cam_pts = 7
        elif has_pullback or has_embedded_media or synced_reveals >= 2:
            cam_pts = 4
            suggestions.append(
                "Kết hợp `REVEAL_PHOTO` (`fill: true` ghim 3D/clip) + `board.sync` + cú kéo lùi `NETWORK_REVEAL` "
                "để tối đa hoá biên đạo camera bảng đen."
            )
        else:
            cam_pts = 1
            suggestions.append("Bổ sung `REVEAL_PHOTO` có media và `NETWORK_REVEAL` ở cuối cho camera 1-shot bảng đen.")

        spatial_links = sum(
            1 for s, rec in zip(shots, recipes)
            if rec in ("connect", "stamp")
            or bool((s.get("board") or {}).get("from"))
            or bool((s.get("board") or {}).get("fill"))
        )
        if spatial_links >= 2:
            trans_pts = 8
        elif spatial_links == 1:
            trans_pts = 5
            suggestions.append("Thêm chỉ đỏ `CONNECT` (`board.from`) hoặc đẩy máy `fill: true` để dẫn mắt giữa các thẻ.")
        else:
            trans_pts = 0
            suggestions.append("Thiếu chỉ đỏ `CONNECT`/`board.from` nối nhân-quả trên bảng điều tra.")
        return max(0, min(MAX_AXES["camera_matchcut"], cam_pts + trans_pts))

    presets = set()
    engines_used = set()
    has_2d_cinematic = False
    has_2d_cam = False
    for sh, (eng, sc) in zip(shots, eng_scenes):
        engines_used.add(eng)
        params = (sh.get("code") or {}).get("params") or {}
        if eng == "three" and sc == "stage":
            pr = (params.get("frame") or {}).get("preset")
            if pr:
                presets.add(str(pr))
            elif params.get("camera"):
                presets.add("custom_camera")
        elif eng == "html":
            if sc in ("xray_cutaway", "dossier", "hero_stat", "scale"):
                has_2d_cinematic = True
            if sc == "scene":
                if params.get("camera"):
                    has_2d_cam = True
                    has_2d_cinematic = True
                if any(isinstance(a, dict) and a.get("z") not in (None, 0) for a in (params.get("actors") or [])):
                    has_2d_cinematic = True

    if fmt == "cinema_3d_film":
        if len(presets) >= 3:
            cam_pts = 7
        elif len(presets) == 2:
            cam_pts = 5
            suggestions.append("Phim 3D 100% nên xoay ≥ 3 góc máy (`ecu_macro`, `low_hero`, `tracking_low`, `dolly_zoom`).")
        else:
            cam_pts = 2
            suggestions.append("Thiếu đa dạng góc máy 3D — dùng ≥ 3 `frame.preset` khác nhau.")
    elif len(presets) >= 2:
        cam_pts = 7
    elif "three" in engines_used and "html" in engines_used and (len(presets) >= 1 or has_2d_cinematic):
        cam_pts = 7
    elif len(engines_used) >= 2 and ("flow" in engines_used or has_2d_cinematic):
        cam_pts = 5
    elif len(presets) == 1 or has_2d_cam or (fmt == "infinite_zoom_journey" and has_2d_cinematic):
        cam_pts = 5 if fmt == "infinite_zoom_journey" and has_2d_cinematic else 3
        if cam_pts < 5:
            suggestions.append(
                "Xoay ít nhất 2 góc máy 3D điện ảnh (`ecu_macro`, `low_hero`, `tracking_low`, "
                "`over_shoulder`, `dolly_zoom`) để tránh lặp góc."
            )
    else:
        cam_pts = 0
        suggestions.append(
            "Thiếu đa dạng góc máy 3D/2D — bổ sung `stage` với ≥ 2 `frame.preset` khác nhau "
            "hoặc trộn góc 2D/3D."
        )

    n_purp = sum(1 for s in shots if s.get("transition_in") in PURPOSEFUL_TRANSITIONS)
    n_agency = sum(1 for s in shots if s.get("transition_in") in AGENCY_TRANSITIONS)
    if n_purp >= 2 or (n_agency >= 1 and len(shots) <= 5):
        trans_pts = 8
    elif n_purp == 1:
        trans_pts = 5
        suggestions.append(
            "Thêm chuyển cảnh chủ đích (`iris_match`, `whip_match`, `tape_stop`) "
            "ở các nhịp bẻ lái/chuyển engine."
        )
    else:
        trans_pts = 0
        suggestions.append(
            "Toàn bộ điểm cắt là `cut` phẳng — dùng `iris_match`, `whip_match` hoặc `tape_stop` "
            "để dẫn mắt liền mạch."
        )

    return max(0, min(MAX_AXES["camera_matchcut"], cam_pts + trans_pts))


def _score_audio_tension(sb, shots, suggestions):
    arch = sb.get("archetype_resolved") or sb.get("archetype")
    arch_cfg = narratives.get_archetype(arch) if arch else None
    has_mood = bool((arch_cfg or {}).get("music_mood") or sb.get("music_mood"))

    per_shot_sfx = [_shot_sfx(s) for s in shots]
    all_sfx = {x for lst in per_shot_sfx for x in lst}
    hook_has_impact = bool(set(per_shot_sfx[0]) & HOOK_IMPACT_SFX) if per_shot_sfx else False

    if hook_has_impact or has_mood:
        p1 = 5
    else:
        p1 = 0
        suggestions.append("Thêm SFX impact cho hook (`sub_drop`/`hit`) hoặc chọn `archetype` để khoá mood nhạc điện ảnh.")

    shots_with_sfx = sum(1 for lst in per_shot_sfx if lst)
    share = shots_with_sfx / max(1, len(shots))
    has_escalation = bool(all_sfx & ESCALATION_SFX)
    if has_escalation or (share >= 0.50 and len(all_sfx) >= 2):
        p2 = 5
    elif share >= 0.30 and len(all_sfx) >= 2:
        p2 = 3
        suggestions.append(
            "Phủ thêm micro-foley/riser (`riser_long`, `paper_rustle`, `neural_pulse`, "
            "`swish_match`) cho ≥ 50% số shot."
        )
    else:
        p2 = 0
        suggestions.append("Âm thanh còn mỏng — bổ sung riser (`riser_long`) và SFX đa dạng ở ≥ 50% số shot.")

    has_contrast_cue = bool(all_sfx & CONTRAST_SFX) or any(s.get("transition_in") == "tape_stop" for s in shots)
    has_twist_beat = any(s.get("beat") == "twist" for s in shots)
    if has_contrast_cue:
        p3 = 5
    elif has_twist_beat and all_sfx:
        p3 = 4
    elif has_twist_beat:
        p3 = 2
        suggestions.append(
            "Gắn cú nhấn âm thanh tương phản (`sting`, `sub_drop`, `tape_stop`, `riser_long`) "
            "cho beat payoff/twist."
        )
    else:
        p3 = 0
        suggestions.append("Thiếu beat `twist` và cú nhấn âm thanh tạo tương phản ở đoạn chốt.")

    return max(0, min(MAX_AXES["audio_tension"], p1 + p2 + p3))


def _score_retention_pacing(sb, shots, suggestions):
    spoken_shots = [s for s in shots if not (s.get("beat") == "outro" and not tts.strip_tags(s.get("vo", "")).strip())]
    durs = [float(s.get("target_sec") or 0) for s in (spoken_shots or shots)]
    total_sec = sum(durs)
    avg = total_sec / max(1, len(durs))
    if 2.2 <= avg <= 4.0:
        p1 = 4
    elif 1.8 <= avg <= 4.5:
        p1 = 2
        suggestions.append(f"Thời lượng shot TB {avg:.2f}s hơi lệch vùng tối ưu 2.2–4.0s.")
    else:
        p1 = 0
        suggestions.append(f"Thời lượng shot TB {avg:.2f}s nằm ngoài chuẩn giữ chân 2.2–4.0s.")

    total_words = sum(lang.word_count(tts.strip_tags(s.get("vo", ""))) for s in (spoken_shots or shots))
    wps = total_words / max(total_sec, 0.1) if total_sec > 0 else 0.0
    if 2.4 <= wps <= 3.6:
        p2 = 3
    elif 2.0 <= wps <= 4.2:
        p2 = 1
        suggestions.append(f"Nhịp lời {wps:.2f} wps hơi lệch vùng trưởng thành 2.4–3.6 wps.")
    else:
        p2 = 0
        suggestions.append(f"Nhịp lời {wps:.2f} wps ngoài chuẩn 2.4–3.6 wps — chỉnh độ dài câu hoặc target_sec.")

    clutter = linter.lint_clutter(sb)
    if not clutter:
        p3 = 3
    elif len(clutter) == 1:
        p3 = 1
        suggestions.append("Còn 1 cảnh báo clutter Vòng 12 — tinh gọn vật thể/chữ on-screen.")
    else:
        p3 = 0
        suggestions.append(f"Có {len(clutter)} cảnh báo clutter Vòng 12 — giảm bớt chữ/vật thể thừa trên khung hình.")

    return max(0, min(MAX_AXES["retention_pacing"], p1 + p2 + p3))


def score_storyboard(sb, history=None):
    """Chấm điểm Agency Viral & Craft (0–100, Format-Agnostic) cho một storyboard dict.

    Trả về:
        {
            "total": int (0..100),
            "grade": "S"|"A"|"B"|"C"|"D",
            "format_family": str,
            "axes": {hook_loop, narrative_freshness, visual_craft, camera_matchcut, audio_tension, retention_pacing},
            "max_axes": {...},
            "suggestions": [str, ...],
        }
    """
    sb = sb or {}
    shots = list(sb.get("shots") or [])
    if not shots:
        axes = {k: 0 for k in MAX_AXES}
        return {
            "total": 0,
            "grade": "D",
            "format_family": "editorial_infographic",
            "axes": axes,
            "max_axes": dict(MAX_AXES),
            "suggestions": ["Storyboard chưa có shot nào."],
        }

    eng_scenes = [_shot_engine_scene(sb, s) for s in shots]
    fmt = detect_format(sb, eng_scenes)
    suggestions = []
    axes = {
        "hook_loop": _score_hook_loop(sb, shots, eng_scenes, fmt, suggestions),
        "narrative_freshness": _score_narrative(sb, shots, eng_scenes, fmt, history, suggestions),
        "visual_craft": _score_visual_craft(sb, shots, eng_scenes, fmt, suggestions),
        "camera_matchcut": _score_camera_matchcut(sb, shots, eng_scenes, fmt, suggestions),
        "audio_tension": _score_audio_tension(sb, shots, suggestions),
        "retention_pacing": _score_retention_pacing(sb, shots, suggestions),
    }
    total = max(0, min(100, int(sum(axes.values()))))
    return {
        "total": total,
        "grade": grade_of(total),
        "format_family": fmt,
        "axes": axes,
        "max_axes": dict(MAX_AXES),
        "suggestions": suggestions,
    }
