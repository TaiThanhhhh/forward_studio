"""Mix & master (sửa lỗ hổng của cartoon-short-kit: SKILL.md nhắc mix.py nhưng zip không có; finish.sh dùng loudnorm
động một lượt làm lệch tỉ lệ voice/nhạc/SFX).

1. lock(): nhận 3 stem (voice, music, sfx), đo GATED RMS từng stem, đặt nhạc = voice + music_db_vs_voice (−6 dB),
   SFX = voice + sfx_db_vs_voice và đỉnh SFX ≤ 0.7 × đỉnh voice. mode "ducking" duck thêm nhạc khi có lời.
   In ra mức đo được để kiểm (nhạc phải hiện −6.0 dB so với voice).
2. master(): đo loudness tích hợp → MỘT gain tuyến tính tới −14 LUFS → limiter true-peak −1 dBTP (oversample ×4)
   → AAC. Độ dài audio = độ dài video (voice + outro), KHÔNG dùng -shortest.
"""
import json
import os
import re

import numpy as np

from .common import CONFIG_DIR, StudioError, db2amp, load_json, probe, replace_retry, run
from .fakes import write_wav


def cfg():
    return load_json(os.path.join(CONFIG_DIR, "mix.json"))


def _db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def gated_rms(a, sr, window_ms=50, abs_db=-45, rel_db=-20):
    """RMS chỉ tính trên các cửa sổ có tín hiệu (bỏ khoảng lặng): cổng tuyệt đối rồi cổng tương đối."""
    if a is None or not len(a):
        return 0.0
    m = a.mean(1) if a.ndim == 2 else a
    w = max(1, int(sr * window_ms / 1000))
    k = len(m) // w
    if k == 0:
        return float(np.sqrt(np.mean(m ** 2)))
    p = (m[: k * w].reshape(k, w) ** 2).mean(1)
    lv = 10 * np.log10(p + 1e-20)
    keep = p[lv > abs_db]
    if not len(keep):
        return 0.0
    mean_db = 10 * np.log10(keep.mean())
    keep = p[(lv > abs_db) & (lv > mean_db + rel_db)]
    return float(np.sqrt(keep.mean())) if len(keep) else 0.0


def envelope(mono, sr, attack_ms, release_ms):
    """Đường bao có lời (0..1) cho ducking."""
    w = int(0.01 * sr)
    m = len(mono) // w + 1
    pad = np.zeros(m * w, np.float32)
    pad[: len(mono)] = np.abs(mono)
    lv = pad.reshape(m, w).max(1)
    active = (lv > 0.02 * (lv.max() + 1e-9)).astype(np.float32)
    a, r = 0.01 / max(attack_ms / 1000, 1e-3), 0.01 / max(release_ms / 1000, 1e-3)
    env = np.zeros(m, np.float32)
    cur = 0.0
    for i in range(m):
        k = a if active[i] > cur else r
        cur += (active[i] - cur) * min(1.0, k)
        env[i] = cur
    return np.repeat(env, w)[: len(mono)]


def lock(voice, music, sfx, sr, mode=None, extra_db=None):
    """Khoá mức 3 stem (float32 (N,2), có thể None) → (mix, báo cáo). extra_db: {'music': x} chỉnh thêm thủ công."""
    c = cfg()
    L = c["level_lock"]
    mode = mode or c.get("mode", "ducking")
    n = max(len(x) for x in (voice, music, sfx) if x is not None)

    def fit(x):
        if x is None:
            return None
        out = np.zeros((n, 2), np.float32)
        out[: len(x)] = x[:n]
        return out

    voice, music, sfx = fit(voice), fit(music), fit(sfx)
    g = dict(window_ms=L["window_ms"], abs_db=L["gate_abs_db"], rel_db=L["gate_rel_db"])
    v_rms = gated_rms(voice, sr, **g) if voice is not None else 0.0
    ref = v_rms if v_rms > 0 else db2amp(c.get("no_voice_ref_dbfs", -20))
    v_peak = float(np.abs(voice).max()) if voice is not None else ref * 4
    rep = {"mode": mode, "voice_gated_rms_db": round(_db(v_rms), 2) if v_rms else None}
    mix = np.zeros((n, 2), np.float32)
    if voice is not None:
        mix += voice
    if music is not None and gated_rms(music, sr, **g) > 0:
        m_rms = gated_rms(music, sr, **g)
        gm = ref * db2amp(L["music_db_vs_voice"] + (extra_db or {}).get("music", 0)) / m_rms
        music = music * gm
        rep["music_db_vs_voice"] = round(_db(gated_rms(music, sr, **g)) - _db(ref), 2)
        if mode == "ducking" and voice is not None:
            d = c["ducking"]
            env = envelope(voice[:, 0], sr, d["attack_ms"], d["release_ms"])
            music = music * (1 - (1 - db2amp(-d["duck_db"])) * env)[:, None]
            rep["ducking_db"] = d["duck_db"]
        mix += music
    if sfx is not None and np.abs(sfx).max() > 0:
        s_rms = gated_rms(sfx, sr, **g) or float(np.sqrt(np.mean(sfx ** 2)))
        gs = ref * db2amp(L["sfx_db_vs_voice"] + (extra_db or {}).get("sfx", 0)) / max(s_rms, 1e-9)
        cap = L["sfx_peak_max_vs_voice_peak"] * v_peak / max(float(np.abs(sfx).max()) * gs, 1e-9)
        gs *= min(1.0, cap)
        sfx = sfx * gs
        rep["sfx_db_vs_voice"] = round(_db(gated_rms(sfx, sr, **g) or 1e-9) - _db(ref), 2)
        rep["sfx_peak_vs_voice_peak"] = round(float(np.abs(sfx).max()) / max(v_peak, 1e-9), 3)
        rep["sfx_peak_capped"] = cap < 1.0
        mix += sfx
    peak = float(np.abs(mix).max())
    rep["pre_master_peak_dbfs"] = round(_db(peak), 2)
    return mix, rep


def lock_files(stems, out_wav, sr=48000):
    """stems = {'voice': path|None, 'music': path|None, 'sfx': path|None} → out_wav. Trả về báo cáo."""
    from . import sfx as sfxlib  # noqa: PLC0415
    arr = {k: (sfxlib.decode(p, sr) if p and os.path.exists(p) else None) for k, p in stems.items()}
    mix, rep = lock(arr.get("voice"), arr.get("music"), arr.get("sfx"), sr)
    write_wav(out_wav, mix, sr)
    return rep


# ------------------------------------------------------------------ master
def measure(path):
    """Loudness tích hợp + true peak (ffmpeg loudnorm, chỉ đo)."""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af",
             "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"], "ffmpeg (đo loudness)")
    txt = r.stderr.decode("utf-8", "replace")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", txt, re.S)
    if not m:
        return None
    d = json.loads(m.group(0))
    return {"lufs": float(d["input_i"]) if d["input_i"] not in ("-inf", "inf") else None,
            "true_peak": float(d["input_tp"]) if d["input_tp"] not in ("-inf", "inf") else None,
            "lra": float(d["input_lra"])}


def master_filter(gain_db):
    m = cfg()["master"]
    lim = db2amp(m["true_peak_db"] - m["limiter_margin_db"])
    sr = 48000
    os_ = int(m.get("oversample", 4))
    return (f"volume={gain_db:.3f}dB,aresample={sr * os_},"
            f"alimiter=limit={lim:.5f}:attack={m['attack_ms']}:release={m['release_ms']}:level=disabled,"
            f"aresample={sr}")


def master(video, wav, out):
    """video (không tiếng) + wav (đã khoá mức) → out.mp4: gain tuyến tính tới LUFS mục tiêu + limiter true-peak.
    Audio được pad/cắt đúng bằng độ dài video (không -shortest)."""
    m = cfg()["master"]
    pre = measure(wav)
    if not pre or pre["lufs"] is None:
        raise StudioError("Không đo được loudness của mix (mix im lặng?).")
    gain = m["lufs"] - pre["lufs"]
    vdur = probe(video)["duration"]
    tmp = out + ".part.mp4"
    from . import encode  # noqa: PLC0415

    def once(g):
        run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
             "-af", master_filter(g) + f",apad,atrim=0:{vdur:.4f}", "-ac", "2", *encode.audio_args(),
             "-t", f"{vdur:.4f}", *encode.mux_args(), tmp], "ffmpeg (master)")
        return measure(tmp) or {}

    post = once(gain)
    # AUD-402: gain tính TRƯỚC limiter nên đầu ra hụt mục tiêu khi limiter làm việc → lượt 2 bù đúng phần hụt
    if post.get("lufs") is not None and abs(post["lufs"] - m["lufs"]) > float(m.get("second_pass_db", 0.3)):
        gain += m["lufs"] - post["lufs"]
        post = once(gain)
    replace_retry(tmp, out)
    return {"input_lufs": round(pre["lufs"], 2), "input_tp": pre["true_peak"], "gain_db": round(gain, 2),
            "output_lufs": post.get("lufs"), "output_tp": post.get("true_peak"), "target_lufs": m["lufs"],
            "target_tp": m["true_peak_db"], "video_sec": round(vdur, 3)}
