"""Agency Viral & Craft Scorecard (Vòng 13 — 0..100 trên 6 trục).

Chấm điểm tự động mức độ điện ảnh, nhịp giữ chân và tính chống lặp "PowerPoint" của một storyboard:
- hook_loop (0..20): Hook ≤ 2.4s, cold-open giàu hình ảnh, không mở bài kiểu bài giảng, có seamless loop.
- narrative_freshness (0..15): có Director Archetype hợp lệ, mạch nhân-quả But/Therefore, re-hook giữa video.
- visual_craft (0..25): tỉ lệ shot giàu chiều sâu ≥ 40%, story_hud, đa dạng beat, phạt chuỗi thẻ phẳng > 2.
- camera_matchcut (0..15): ≥ 2 góc máy 3D điện ảnh (hoặc trộn góc 2D/3D) + chuyển cảnh chủ đích.
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
    "visual_craft": "Mỹ thuật & Chiều sâu (Anti-PowerPoint)",
    "camera_matchcut": "Góc máy 3D & Match Cut",
    "audio_tension": "Đường cong âm thanh & SFX",
    "retention_pacing": "Nhịp giữ chân & Visual Budget",
}

COLD_OPEN_SCENES = frozenset({"drop", "stage", "scene", "xray_cutaway", "dossier", "hero_stat"})
RICH_SCENES = frozenset({"dossier", "xray_cutaway", "hero_stat", "stage"})
FLAT_CARDS = frozenset({"title", "fact", "counter", "compare"})
PURPOSEFUL_TRANSITIONS = frozenset({"iris_match", "whip_match", "tape_stop", "match", "whip"})
AGENCY_TRANSITIONS = frozenset({"iris_match", "whip_match", "tape_stop"})
HOOK_IMPACT_SFX = frozenset({"sub_drop", "boom", "hit", "impact", "sting", "thud", "whoosh", "swish_match", "tape_stop"})
ESCALATION_SFX = frozenset({"riser", "riser_long", "heartbeat", "neural_pulse", "paper_rustle", "tick"})
CONTRAST_SFX = frozenset({"hit", "sting", "sting_low", "boom", "sub_drop", "tape_stop", "riser_long"})

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


def _score_hook_loop(sb, shots, eng_scenes, suggestions):
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

    if sc0 in COLD_OPEN_SCENES or eng0 == "flow":
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

    if _has_explicit_loop(sb, shots):
        pts += 4
    else:
        suggestions.append("Dùng `outro.mode: \"loop\"` (hoặc câu cầu nối vòng lặp) để đẩy AVD > 100%.")
    return max(0, min(MAX_AXES["hook_loop"], pts))


def _score_narrative(sb, shots, eng_scenes, history, suggestions):
    pts = 0
    valid_archs = set(narratives.archetype_ids())
    arch = sb.get("archetype_resolved") or sb.get("archetype")
    if arch in valid_archs:
        pts += 4
    else:
        suggestions.append("Khai báo `archetype` hợp lệ (1 trong 6 Director Archetypes trong `config/archetypes.json`).")

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
            if eng_switch or trans_interrupt or vo_contrast:
                has_rehook = True
                break
    if has_rehook:
        pts += 5
    else:
        suggestions.append(
            "Thêm Mid-Video Re-Hook ở nửa giữa video (đổi engine, dùng "
            "`iris_match`/`tape_stop`/`whip_match`, hoặc bẻ lái bằng từ nối tương phản)."
        )

    if history and arch and isinstance(history, list):
        recent_archs = [
            h.get("archetype_resolved") or h.get("archetype")
            for h in history[:2]
            if isinstance(h, dict)
        ]
        if arch in recent_archs:
            pts = max(0, pts - 2)
            suggestions.append(f"Archetype `{arch}` trùng video gần nhất — xoay sang phong cách đạo diễn khác.")

    return max(0, min(MAX_AXES["narrative_freshness"], pts))


def _score_visual_craft(sb, shots, eng_scenes, suggestions):
    n = max(1, len(shots))
    rich_count = 0
    for sh, (eng, sc) in zip(shots, eng_scenes):
        params = (sh.get("code") or {}).get("params") or {}
        if sc in RICH_SCENES or eng == "flow":
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
    hud_pts = 4 if has_hud else 0

    unique_scenes = len({sc for _, sc in eng_scenes if sc})
    div_pts = round(7 * min(1.0, unique_scenes / 5.0))
    if unique_scenes < 5:
        suggestions.append(f"Mới dùng {unique_scenes} loại beat/cảnh khác nhau (mục tiêu ≥ 5) — đa dạng hoá nhịp hình.")

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


def _score_camera_matchcut(shots, eng_scenes, suggestions):
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
            if sc in ("xray_cutaway", "dossier", "hero_stat"):
                has_2d_cinematic = True
            if sc == "scene":
                if params.get("camera"):
                    has_2d_cam = True
                    has_2d_cinematic = True
                if any(isinstance(a, dict) and a.get("z") not in (None, 0) for a in (params.get("actors") or [])):
                    has_2d_cinematic = True

    if len(presets) >= 2:
        cam_pts = 7
    elif "three" in engines_used and "html" in engines_used and (len(presets) >= 1 or has_2d_cinematic):
        cam_pts = 7
    elif len(engines_used) >= 2 and ("flow" in engines_used or has_2d_cinematic):
        cam_pts = 5
    elif len(presets) == 1 or has_2d_cam:
        cam_pts = 3
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
    durs = [float(s.get("target_sec") or 0) for s in shots]
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

    total_words = sum(lang.word_count(tts.strip_tags(s.get("vo", ""))) for s in shots)
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
    """Chấm điểm Agency Viral & Craft (0–100) cho một storyboard dict.

    Trả về:
        {
            "total": int (0..100),
            "grade": "S"|"A"|"B"|"C"|"D",
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
            "axes": axes,
            "max_axes": dict(MAX_AXES),
            "suggestions": ["Storyboard chưa có shot nào."],
        }

    eng_scenes = [_shot_engine_scene(sb, s) for s in shots]
    suggestions = []
    axes = {
        "hook_loop": _score_hook_loop(sb, shots, eng_scenes, suggestions),
        "narrative_freshness": _score_narrative(sb, shots, eng_scenes, history, suggestions),
        "visual_craft": _score_visual_craft(sb, shots, eng_scenes, suggestions),
        "camera_matchcut": _score_camera_matchcut(shots, eng_scenes, suggestions),
        "audio_tension": _score_audio_tension(sb, shots, suggestions),
        "retention_pacing": _score_retention_pacing(sb, shots, suggestions),
    }
    total = max(0, min(100, int(sum(axes.values()))))
    return {
        "total": total,
        "grade": grade_of(total),
        "axes": axes,
        "max_axes": dict(MAX_AXES),
        "suggestions": suggestions,
    }
