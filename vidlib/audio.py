"""Âm thanh: CHỈ xuất stems (voice / music / sfx) — việc khoá mức và cộng do mix.py làm (đúng hợp đồng của kit).

Tiếng Flow đã bị bỏ từ lúc ingest; âm thanh cuối chỉ gồm VO + nhạc + SFX của pipeline.
- SFX (cue table): điểm cắt (transition), chữ text_fx bật lên/đập xuống/nổ văng, `sfx` từng shot (tên, hoặc
  {"name", "at": giây trong shot | "vo:<từ>"}), `cues` của storyboard, cue của shot code, preset payoff.
  Cân bằng GIỮA các SFX theo channel.json → audio.sfx_db; mức của cả stem do mix.py khoá theo giọng.
- Nhạc: audio/music.* của dự án; không có thì tổng hợp (musicgen) nếu mix.json → music.synth_if_missing.
  Preset payoff: nhạc DỪNG ở câu twist, một nhịp hit trầm.
- Beat: bắt BPM từ nhạc để snap điểm cắt (timeline.snap_to_beats).
"""
import os

import numpy as np

from . import mix as mixlib
from . import musicgen
from . import sfx as sfxlib
from .common import AUDIO_EXT, FPS, channel, db2amp, find_file
from .fakes import write_wav


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


def sfx_events(sb, tl, text_sfx=(), vo=None, code_cues=()):
    """[(giây, tên)] — đã khử trùng (cùng tên trong 0.12s)."""
    auto = channel()["audio"]["auto_sfx"]
    lead = channel()["vo"].get("react_lead_default", 2) / FPS
    ev = []
    shots = {s["id"]: (i, s) for i, s in enumerate(sb["shots"])}
    for seg in tl["segments"]:
        t0 = seg["start_f"] / FPS
        if seg["sid"] == "OUTRO":
            if seg["transition"] in auto:
                ev.append((t0 - 0.06, auto[seg["transition"]]))
            ev.append((t0 + 0.45, auto.get("outro", "pop")))
            continue
        tr = seg["transition"]
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
    info = {"music": None, "music_stop": None}
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
                i0 = int(max(0.0, stop - 0.06) * sr)
                m[i0:] *= (np.linspace(1, 0, n - i0) ** 8)[:, None]
            fade = int(0.6 * sr)
            m[-fade:] *= np.linspace(1, 0, fade)[:, None]
            music = m
            info["music"] = os.path.basename(music_path)
    elif mcfg["music"].get("synth_if_missing"):
        bpm = mcfg["music"].get("bpm", 112)
        try:                                           # style có thể đặt nhịp nhạc riêng (styles/<id>.json → music.bpm)
            from . import textstyle  # noqa: PLC0415
            bpm = (textstyle.load_style(sb.get("style_resolved") or sb.get("style")).get("music") or {}).get("bpm") or bpm
        except Exception:  # noqa: BLE001
            pass
        music = musicgen.bed(tl["duration"], stop_at=stop, bpm=bpm)[:n]
        info["music"] = f"tổng hợp (musicgen, {bpm} BPM)"
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
            "music_stop": info["music_stop"], "levels": rep, "vo": vo is not None,
            "ducking_db": rep.get("ducking_db", 0), "stems": {k: v for k, v in paths.items() if v}}
