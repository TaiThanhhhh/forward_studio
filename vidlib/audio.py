"""Âm thanh: CHỈ xuất stems (voice / music / sfx) — việc khoá mức và cộng do mix.py làm (đúng hợp đồng của kit).

Tiếng Flow đã bị bỏ từ lúc ingest; âm thanh cuối chỉ gồm VO + nhạc + SFX của pipeline.
- SFX (cue table): điểm cắt (transition), chữ text_fx bật lên/đập xuống/nổ văng, `sfx` từng shot (tên, hoặc
  {"name", "at": giây trong shot | "vo:<từ>"}), `cues` của storyboard, cue của shot code, preset payoff,
  và Audio-Driven Tension Arc / Micro-Foley tự động (Vòng 13: hook sub_drop, match-cut swish_match,
  tape_stop, dossier paper_rustle, xray_cutaway neural_pulse, pre-climax riser_long).
  Cân bằng GIỮA các SFX theo channel.json → audio.sfx_db; mức của cả stem do mix.py khoá theo giọng.
- Nhạc: audio/music.* của dự án; không có thì tổng hợp (musicgen) với mood tự chọn theo archetype/style +
  cue_times đường cong năng lượng + Dramatic Dead-Air Drop trước twist.
- Beat: bắt BPM từ nhạc để snap điểm cắt (timeline.snap_to_beats).
"""
import json
import os

import numpy as np

from . import mix as mixlib
from . import musicgen
from . import sfx as sfxlib
from .common import AUDIO_EXT, CONFIG_DIR, FPS, channel, db2amp, find_file
from .fakes import write_wav

ARCHETYPE_MOOD = {
    "visceral_anatomy": "visceral_thriller",
    "forensic_dossier": "investigative_pulse",
    "editorial_clash": "kinetic_editorial",
    "ticking_clock": "clockwork_tension",
    "myth_autopsy": "investigative_pulse",
    "one_object_odyssey": "minimal_cinematic",
}

_HEAVY_IMPACT_SFX = frozenset({"sub_drop", "boom", "impact", "hit", "sting", "sting_low"})
_RISER_SFX = frozenset({"riser", "riser_long"})
_SWISH_SFX = frozenset({"swish_match", "whoosh", "whoosh_soft"})


def music_file(proj):
    return find_file(os.path.join(proj, "audio"), ["music", "nhac", "bgm"], AUDIO_EXT)


def detect_beats(mono, sr, duration=None):
    """Ước lượng BPM (70–180) bằng tự tương quan đường bao onset; trả về (bpm, mảng thời điểm beat)."""
    hop = 512
    n = len(mono) // hop
    if n < 64:
        return None, np.array([])
    env = np.sqrt((mono[: n * hop].reshape(n, hop) ** 2).mean(1))
    on = np.maximum(0, np.diff(env, prepend=env[0]))
    on = on - on.mean()
    fr = sr / hop
    lags = np.arange(int(fr * 60 / 180), int(fr * 60 / 70) + 1)
    ac = np.array([np.dot(on[:-lag], on[lag:]) for lag in lags])
    lag = int(lags[int(np.argmax(ac))])
    bpm = 60 * fr / lag
    phases = [on[p::lag].sum() for p in range(lag)]
    p0 = int(np.argmax(phases))
    dur = duration or len(mono) / sr
    beats = np.arange(p0 / fr, dur, lag / fr)
    return round(float(bpm), 1), beats


def twist_time(tl, sb):
    """Thời điểm bắt đầu shot twist đầu tiên (giây) hoặc None."""
    beats = {s["id"]: s.get("beat") for s in sb["shots"]}
    for seg in tl["segments"]:
        if beats.get(seg["sid"]) == "twist":
            return seg["start_f"] / FPS
    return None


def cue_times(tl, sb):
    """Trích mốc năng lượng {'escalate_at', 'payoff_at', 'twist_at'} (giây) cho musicgen.bed."""
    beats = {s["id"]: s.get("beat") for s in sb.get("shots") or []}
    found = {}
    for seg in tl.get("segments") or []:
        b = beats.get(seg["sid"])
        if b == "escalate" and "escalate_at" not in found:
            found["escalate_at"] = round(seg["start_f"] / FPS, 3)
        elif b == "payoff" and "payoff_at" not in found:
            found["payoff_at"] = round(seg["start_f"] / FPS, 3)
        elif b == "twist" and "twist_at" not in found:
            found["twist_at"] = round(seg["start_f"] / FPS, 3)
    return found


def _infer_mood_from_text(text):
    """Ánh xạ mô tả mood text trong styles/*.json → 1 trong 5 mood của musicgen."""
    s = (text or "").lower()
    if not s:
        return "kinetic_editorial"
    if any(k in s for k in ("heartbeat", "drone", "thriller", "clinical", "ominous", "horror", "x-ray")):
        return "visceral_thriller"
    if any(k in s for k in ("clock", "tick", "tension", "motorik", "techno", "industrial", "countdown")):
        return "clockwork_tension"
    if any(k in s for k in ("dark", "sub bass", "investigative", "noir", "mystery", "spy", "synthwave")):
        return "investigative_pulse"
    minimal_kw = (
        "piano", "ambient", "minimal", "glassy", "soft", "strings",
        "acoustic", "chậm", "tối giản", "suy tư", "thong thả",
    )
    if any(k in s for k in minimal_kw):
        return "minimal_cinematic"
    return "kinetic_editorial"


def resolve_music_mood(sb, style_cfg=None):
    """Chọn mood nhạc nền từ storyboard (music_mood / archetype) hoặc suy ra từ style.music.mood."""
    direct = sb.get("music_mood")
    if direct in musicgen.MOODS:
        return direct

    arch = sb.get("archetype") or sb.get("director_archetype")
    if isinstance(arch, dict):
        m = arch.get("music_mood")
        if m in musicgen.MOODS:
            return m
        arch = arch.get("id")
    if isinstance(arch, str) and arch:
        if arch in ARCHETYPE_MOOD:
            return ARCHETYPE_MOOD[arch]
        arch_path = os.path.join(CONFIG_DIR, "archetypes.json")
        if os.path.exists(arch_path):
            try:
                with open(arch_path, encoding="utf-8") as f:
                    data = json.load(f)
                entry = (data.get("archetypes") or data).get(arch)
                if isinstance(entry, dict) and entry.get("music_mood") in musicgen.MOODS:
                    return entry["music_mood"]
            except Exception:  # noqa: BLE001
                pass

    style_mood = ((style_cfg or {}).get("music") or {}).get("mood")
    if style_mood in musicgen.MOODS:
        return style_mood
    return _infer_mood_from_text(style_mood)


def _word_time(vo, word, shot_idx, lead):
    from .textfx import _fold  # noqa: PLC0415
    if not vo:
        return None
    want = _fold(word)
    for ln in vo["lines"]:
        if shot_idx in ln["shots"] or ln["shots"][0] <= shot_idx:
            for w in ln["words"]:
                if want and want in _fold(w["w"]):
                    return w["start"] - lead
    return None


def _has_near(events, t, names, window=0.25):
    return any(abs(et - t) <= window and sfxlib.split_name(en)[0] in names for et, en in events)


def sfx_events(sb, tl, text_sfx=(), vo=None, code_cues=()):
    """[(giây, tên)] — đã khử trùng (cùng tên trong 0.12s) + tự bơm micro-foley & tension arc."""
    auto = channel()["audio"]["auto_sfx"]
    lead = channel()["vo"].get("react_lead_default", 2) / FPS
    ev = []
    shots = {s["id"]: (i, s) for i, s in enumerate(sb["shots"])}

    # Bước 1: thu thập toàn bộ SFX tường minh (transition cấu hình sẵn, shot.sfx, cues, text_sfx, code_cues)
    for seg in tl["segments"]:
        t0 = seg["start_f"] / FPS
        if seg["sid"] == "OUTRO":
            tr_out = seg.get("transition")
            if tr_out in auto:
                ev.append((t0 - 0.06, auto[tr_out]))
            elif tr_out in ("iris_match", "whip_match"):
                ev.append((max(0.0, t0 - 0.08), "swish_match"))
            elif tr_out == "tape_stop":
                ev.append((max(0.0, t0 - 0.08), "tape_stop"))
            ev.append((t0 + 0.45, auto.get("outro", "pop")))
            continue
        tr = seg.get("transition")
        if tr in auto and seg["index"] > 0:
            ev.append((t0 - (0.06 if tr == "whip" else 0.0), auto[tr]))
        idx, shot = shots[seg["sid"]]
        for x in shot.get("sfx") or []:
            if isinstance(x, str):
                ev.append((t0 + 0.02, x))
                continue
            at = x.get("at", 0.02)
            if isinstance(at, str) and at.startswith("vo:"):
                t = _word_time(vo, at[3:], idx, lead)
                if t is not None:
                    ev.append((t, x["name"]))
            else:
                ev.append((t0 + float(at) * seg["scale"], x["name"]))
    for c in sb.get("cues") or []:
        ev.append((float(c["t"]), c["name"]))
    ev += list(text_sfx) + list(code_cues)

    # Bước 2: tự động tiêm Audio-Driven Tension Arc & Micro-Foley (không trùng nếu shot đã đặt tường minh)
    auto_ev = []
    payoff_t = None
    twist_t = None
    for seg in tl["segments"]:
        if seg["sid"] == "OUTRO":
            continue
        t0 = seg["start_f"] / FPS
        _, shot = shots[seg["sid"]]
        beat = shot.get("beat")
        if beat == "payoff" and payoff_t is None:
            payoff_t = t0
        if beat == "twist" and twist_t is None:
            twist_t = t0

        # 1) Hook frame 0: sub_drop nếu hook chưa có cú chạm trầm
        if seg["index"] == 0:
            if not _has_near(ev, t0, _HEAVY_IMPACT_SFX, window=0.35):
                auto_ev.append((t0, "sub_drop"))

        # 2) Chuyển cảnh Agency: iris_match / whip_match → swish_match; tape_stop → tape_stop
        tr = seg.get("transition") or shot.get("transition_in")
        if seg["index"] > 0:
            if tr in ("iris_match", "whip_match"):
                if not _has_near(ev, t0, _SWISH_SFX, window=0.22):
                    auto_ev.append((max(0.0, t0 - 0.08), "swish_match"))
            elif tr == "tape_stop":
                if not _has_near(ev, t0, {"tape_stop"}, window=0.25):
                    auto_ev.append((max(0.0, t0 - 0.08), "tape_stop"))

        # 3) Micro-foley theo beat điện ảnh: dossier → paper_rustle; xray_cutaway → neural_pulse
        scene = (shot.get("code") or {}).get("scene")
        if scene == "dossier":
            if not _has_near(ev, t0, {"paper_rustle"}, window=0.30):
                auto_ev.append((t0 + 0.04, "paper_rustle"))
        elif scene == "xray_cutaway":
            if not _has_near(ev, t0, {"neural_pulse"}, window=0.30):
                auto_ev.append((t0 + 0.04, "neural_pulse"))

    # 4) Riser dài 1.8s hạ cánh đúng điểm chuyển sang twist (hoặc payoff nếu không có twist)
    climax_t = twist_t if (twist_t is not None and twist_t >= 2.0) else (
        payoff_t if (payoff_t is not None and payoff_t >= 2.0) else None
    )
    if climax_t is not None:
        has_riser = any(
            (climax_t - 2.4) <= et <= (climax_t + 0.2) and sfxlib.split_name(en)[0] in _RISER_SFX
            for et, en in ev
        )
        if not has_riser:
            auto_ev.append((max(0.0, climax_t - 1.8), "riser_long"))

    ev.extend(auto_ev)
    ev.sort()
    out = []
    for t, name in ev:
        if out and name == out[-1][1] and t - out[-1][0] < 0.12:
            continue
        if any(abs(t - t2) < 0.05 and n2 == name for t2, n2 in out):
            continue
        out.append((round(max(0.0, t), 3), name))
    return out


def build_stems(proj, sb, tl, vo, events, music_path, stem_dir):
    """Ghi stems/voice.wav, music.wav, sfx.wav. Trả về (dict đường dẫn, thông tin)."""
    cfg = channel()["audio"]
    mcfg = mixlib.cfg()
    sr = cfg["sample_rate"]
    os.makedirs(stem_dir, exist_ok=True)
    n = int(np.ceil(tl["duration"] * sr)) + sr // 10
    paths = {"voice": None, "music": None, "sfx": None}
    info = {"music": None, "music_stop": None, "music_mood": None}
    if vo is not None:
        v = np.zeros((n, 2), np.float32)
        a = vo["audio"][:n]
        v[: len(a)] = a
        paths["voice"] = os.path.join(stem_dir, "voice.wav")
        write_wav(paths["voice"], v, sr)
    stop = twist_time(tl, sb) if mcfg["payoff"].get("music_stop") else None
    music = None
    if music_path:
        m = sfxlib.decode(music_path, sr)
        if len(m):
            m = np.tile(m, (int(np.ceil(n / len(m))), 1))[:n]
            if stop:
                dead = min(0.35, stop * 0.45)
                i0 = int(max(0.0, stop - dead) * sr)
                cut_n = min(int(0.045 * sr), max(1, n - i0))
                m[i0 : i0 + cut_n] *= (np.linspace(1, 0, cut_n) ** 4)[:, None]
                m[i0 + cut_n :] = 0.0
            fade = min(int(0.6 * sr), len(m))
            m[-fade:] *= np.linspace(1, 0, fade)[:, None]
            music = m
            info["music"] = os.path.basename(music_path)
    elif mcfg["music"].get("synth_if_missing"):
        bpm = mcfg["music"].get("bpm", 112)
        style_cfg = None
        try:                                           # style có thể đặt nhịp/mood riêng (styles/<id>.json → music)
            from . import textstyle  # noqa: PLC0415
            style_cfg = textstyle.load_style(sb.get("style_resolved") or sb.get("style"))
            bpm = (style_cfg.get("music") or {}).get("bpm") or bpm
        except Exception:  # noqa: BLE001
            pass
        mood = resolve_music_mood(sb, style_cfg)
        cues = cue_times(tl, sb)
        seed = int(sb.get("music_seed", 7))
        music = musicgen.bed(tl["duration"], stop_at=stop, bpm=bpm, seed=seed, mood=mood, cue_times=cues)[:n]
        info["music"] = f"tổng hợp (musicgen, {mood}, {bpm} BPM)"
        info["music_mood"] = mood
    if music is not None:
        mm = np.zeros((n, 2), np.float32)
        mm[: len(music)] = music
        paths["music"] = os.path.join(stem_dir, "music.wav")
        write_wav(paths["music"], mm, sr)
        info["music_stop"] = stop
    s = np.zeros((n, 2), np.float32)
    for t, name in events:
        a = sfxlib.load(name, sr)
        i0 = int(round(t * sr))
        a = a[: max(0, n - i0)]
        s[i0:i0 + len(a)] += a * db2amp(sfxlib.level_db(name))
    if np.abs(s).max() > 0:
        paths["sfx"] = os.path.join(stem_dir, "sfx.wav")
        write_wav(paths["sfx"], s, sr)
    return paths, info


def mix(proj, sb, tl, vo, text_sfx, music_path, out_wav, code_cues=()):
    """Cue table → stems → mix.py khoá mức → out_wav (chưa master)."""
    events = sfx_events(sb, tl, text_sfx, vo, code_cues)
    mcfg = mixlib.cfg()
    stop = twist_time(tl, sb)
    if stop and mcfg["payoff"].get("hit") and not any(abs(t - stop) < 0.1 for t, _ in events):
        events = sorted(events + [(round(stop, 3), mcfg["payoff"]["hit"])])
    stem_dir = os.path.join(os.path.dirname(out_wav), "stems")
    paths, info = build_stems(proj, sb, tl, vo, events, music_path, stem_dir)
    rep = mixlib.lock_files(paths, out_wav, channel()["audio"]["sample_rate"])
    return {"sfx": [{"t": t, "name": nm, "db": sfxlib.level_db(nm)} for t, nm in events], "music": info["music"],
            "music_mood": info.get("music_mood"), "music_stop": info["music_stop"], "levels": rep,
            "vo": vo is not None, "ducking_db": rep.get("ducking_db", 0),
            "stems": {k: v for k, v in paths.items() if v}}
