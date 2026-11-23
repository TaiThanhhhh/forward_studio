"""Thư viện SFX cục bộ: assets/sfx/<tên>.wav (file của bạn được ưu tiên) + âm thanh tự tổng hợp bằng code
(không lo bản quyền, sinh lần đầu vào assets/sfx/_builtin/).

Muốn tiếng "xịn" hơn: bỏ file CC0 vào assets/sfx/ đúng tên (vd assets/sfx/boom.wav).
"""
import os
import subprocess
import wave

import numpy as np

from .common import SFX_DIR, StudioError, channel, ffbin

BUILTIN_DIR = os.path.join(SFX_DIR, "_builtin")
GEN_SR = 44100  # tốc độ tổng hợp; decode() đổi sang sample rate của pipeline

DESCRIPTIONS = {
    "whoosh": "lướt nhanh, chuyển cảnh whip",
    "whoosh_soft": "lướt nhẹ",
    "pop": "chữ/vật bật lên",
    "hit": "va chạm gọn, lộ kết quả (flash)",
    "boom": "nổ trầm, thảm hoạ",
    "impact": "va chạm mạnh có đuôi",
    "thud": "chạm nhẹ",
    "tick": "tích tắc, bộ đếm",
    "click": "bấm, khớp",
    "riser": "dâng căng thẳng trước reveal",
    "ding": "đúng, tích cực",
    "warn": "cảnh báo",
    "glitch": "lỗi số",
    "sparkle": "lấp lánh",
    "heartbeat": "nhịp tim",
    # từ cartoon-short-kit (example/soldier/audio.py), chỉnh cho kênh thí nghiệm
    "thunk": "gõ/đặt mạnh xuống (cân, đặt cốc)",
    "rumble": "rung trầm kéo dài (sụp đổ, sôi bùng)",
    "crash": "đổ vỡ nhiều mảnh",
    "scrape": "kim loại cạ",
    "ting": "lấp lánh kim loại, reveal",
    "sting": "nhấn twist: trầm + stab",
    "sting_low": "nhấn twist chỉ có tiếng trầm (preset payoff)",
    "creak": "kẽo kẹt",
    "snap": "gãy",
    "splash": "rơi xuống nước",
    "sizzle": "xèo — vật nóng chạm nước",
    "bubbles": "sôi lục bục",
    # từ sound_bed.py của kaz-documentary (engine board, vòng 6). Tên có tham số: "<tên>:<giây>" (vd typing:0.8)
    "typing": "gõ máy chữ 22 ký tự/giây (nhãn băng dính) — typing:<giây>",
    "stamp": "đóng dấu: thud trầm + tiếng giấy",
    "scratch": "bút dạ khoanh tròn / gạch — scratch:<giây>",
    "projector": "máy chiếu phim lạch cạch 24/giây + hiss (đoạn chèn phim câm) — projector:<giây>",
}
PARAM_SFX = ("typing", "scratch", "projector")


def split_name(name):
    """'typing:0.8' → ('typing', 0.8); 'boom' → ('boom', None)."""
    base, _, arg = str(name).partition(":")
    try:
        return base, (round(float(arg), 1) if arg else None)
    except ValueError:
        return base, None


def _t(d):
    return np.arange(int(d * GEN_SR)) / GEN_SR


def _lowpass(x, cut):
    cut = np.broadcast_to(np.asarray(cut, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cut / GEN_SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def _noise(d, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, int(d * GEN_SR))


def _lp_fast(x, cutoff):
    """Low-pass FFT (nhanh, đủ cho SFX dài) — từ cartoon-short-kit."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / GEN_SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def _hp_fast(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / GEN_SR)
    X *= 1 - 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def _thunk(f0=90, d=0.3, seed=31):
    t = _t(d)
    return (np.sin(2 * np.pi * f0 * t * (1 + 0.6 * np.exp(-t * 40))) * np.exp(-t * 14)
            + _lp_fast(_noise(d, seed), 1200) * np.exp(-t * 30) * 0.5)


def _brass(freqs, d):
    t = _t(d)
    s = np.zeros(len(t))
    for f in freqs:
        ph = 2 * np.pi * f * t + 0.003 * np.sin(2 * np.pi * 5 * t)
        s += sum(np.sin((k + 1) * ph) / (k + 1) ** 1.3 for k in range(8))
    a = np.minimum(1, t / 0.08) * np.clip(np.minimum(1, (d - t) / 0.15), 0, 1)
    return _lp_fast(s * a, 1800) / len(freqs)


def _midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def _sweep(f0, f1, d, curve=2.0):
    t = _t(d)
    f = f1 + (f0 - f1) * np.exp(-curve * t / d * 3)
    return np.sin(2 * np.pi * np.cumsum(f) / GEN_SR)


def _click(seed):
    n = int(0.03 * GEN_SR)
    return np.random.default_rng(seed).normal(0, 1, n) * np.exp(-np.arange(n) / GEN_SR * 250)


def _make_param(base, dur):
    """SFX có độ dài theo tham số (port sound_bed.py của kaz-documentary)."""
    dur = max(0.1, float(dur or 0.5))
    n = int((dur + 0.15) * GEN_SR)
    out = np.zeros(n)
    rng = np.random.default_rng(int(dur * 100) + len(base))
    if base == "typing":  # một click mỗi ký tự, 22 ký tự/giây
        for j in range(int(dur * 22) + 1):
            c = _click(j) * rng.uniform(0.7, 1.0)
            i = int(j / 22 * GEN_SR + rng.uniform(-0.004, 0.004) * GEN_SR)
            i = max(0, i)
            out[i:i + len(c)] += c[: max(0, n - i)]
        return _hp_fast(out, 900)
    if base == "scratch":  # bút dạ cạ giấy: nhiễu điều biến ~14 Hz, lọc dải
        L = int(dur * GEN_SR)
        t = np.arange(L) / GEN_SR
        x = rng.normal(0, 1, L) * 0.5 * (1 + np.sin(t * 90)) * np.minimum(1, t / 0.02) * np.minimum(1, (dur - t) / 0.04)
        out[:L] = _hp_fast(_lp_fast(x, 5200), 1400)
        return out
    if base == "projector":  # lạch cạch 24/giây + hiss
        L = int(dur * GEN_SR)
        m = int(0.012 * GEN_SR)
        for k in range(int(dur * 24)):
            p0 = int(k * GEN_SR / 24)
            if p0 + m < L:
                out[p0:p0 + m] += rng.normal(0, 1, m) * np.exp(-np.arange(m) / GEN_SR * 400) * 3
        out[:L] += rng.normal(0, 1, L) * 1.0
        return _lp_fast(out, 7000)
    raise KeyError(base)


def _make(name):  # noqa: C901 — bảng tổng hợp
    if name == "stamp":  # thud của sound_bed.py: tần số trượt 110→40 Hz + tiếng giấy
        t = _t(1.2)
        return (np.sin(2 * np.pi * (70 * np.exp(-t * 6) + 40) * t) * np.exp(-t * 7)
                + 0.3 * _noise(1.2, 51) * np.exp(-t * 40))
    if name == "whoosh":
        d = 0.5
        tt = _t(d) / d
        return _lowpass(_noise(d, 1), 300 + 4200 * np.sin(np.pi * tt) ** 2) * np.sin(np.pi * tt) ** 1.5 * 1.6
    if name == "whoosh_soft":
        d = 0.8
        tt = _t(d) / d
        return _lowpass(_noise(d, 2), 200 + 1600 * np.sin(np.pi * tt) ** 2) * np.sin(np.pi * tt) ** 2 * 1.4
    if name == "pop":
        d = 0.12
        t = _t(d)
        return _sweep(900, 380, d, 4) * np.exp(-t * 32)
    if name == "hit":
        d = 0.35
        t = _t(d)
        return _sweep(160, 50, d, 3) * np.exp(-t * 14) * 0.9 + _lowpass(_noise(d, 21), 3500) * np.exp(-t * 45)
    if name == "boom":
        d = 1.6
        t = _t(d)
        body = _sweep(70, 28, d, 1.5) * np.exp(-t * 2.6)
        rumble = _lowpass(_noise(d, 22), 220) * np.exp(-t * 2.0) * 2.2
        crack = _lowpass(_noise(d, 23), 2600) * np.exp(-t * 22)
        return body + rumble + crack * 0.7
    if name == "impact":
        d = 0.9
        t = _t(d)
        return _sweep(110, 38, d) * np.exp(-t * 6) * 0.9 + _lowpass(_noise(d, 3), 2500) * np.exp(-t * 30) * 0.9
    if name == "thud":
        d = 0.35
        t = _t(d)
        return _sweep(140, 60, d) * np.exp(-t * 14) + _lowpass(_noise(d, 4), 900) * np.exp(-t * 40) * 0.5
    if name == "tick":
        d = 0.06
        t = _t(d)
        return (np.sin(2 * np.pi * 3200 * t) + np.sin(2 * np.pi * 5100 * t) * 0.4) * np.exp(-t * 160) * 0.8
    if name == "click":
        d = 0.04
        t = _t(d)
        return (np.sin(2 * np.pi * 2400 * t) * 0.6 + _noise(d, 5) * 0.5) * np.exp(-t * 180)
    if name == "riser":
        d = 1.4
        t = _t(d)
        f = 180 * (1 + 3 * (t / d) ** 2)
        tone = np.sin(2 * np.pi * np.cumsum(f) / GEN_SR) * 0.35
        return (tone + _lowpass(_noise(d, 8), 400 + 5000 * (t / d) ** 2) * 0.8) * (t / d) ** 1.6
    if name == "ding":
        d = 1.0
        t = _t(d)
        return (np.sin(2 * np.pi * 988 * t) + np.sin(2 * np.pi * 1482 * t) * 0.5) * np.exp(-t * 4) * 0.6
    if name == "warn":
        d = 0.55
        t = _t(d)
        tone = np.sign(np.sin(2 * np.pi * 190 * t)) * 0.3 + np.sin(2 * np.pi * 380 * t) * 0.3
        return _lowpass(tone * ((t % 0.27) < 0.18), 1800) * 1.2
    if name == "glitch":
        d = 0.35
        rng = np.random.default_rng(12)
        x = np.repeat(rng.uniform(-1, 1, int(d * GEN_SR) // 60 + 1), 60)[: int(d * GEN_SR)]
        gate = np.repeat(rng.random(int(d * 40) + 1) > 0.4, GEN_SR // 40 + 1)[: len(x)]
        return x * gate * 0.5
    if name == "sparkle":
        d = 0.8
        out = np.zeros(int(d * GEN_SR))
        rng = np.random.default_rng(11)
        for _ in range(9):
            i = int(rng.uniform(0, 0.5) * GEN_SR)
            seg = np.sin(2 * np.pi * rng.uniform(2500, 5500) * _t(0.25)) * np.exp(-_t(0.25) * 22) * rng.uniform(.2, .5)
            out[i:i + len(seg)] += seg[: len(out) - i]
        return out
    if name == "heartbeat":
        d = 0.8
        out = np.zeros(int(d * GEN_SR))
        for st, g in ((0.0, 1.0), (0.24, 0.7)):
            seg = _make("thud") * g
            i = int(st * GEN_SR)
            out[i:i + len(seg)] += seg[: len(out) - i]
        return _lowpass(out, 400) * 2.2
    if name == "thunk":
        return _thunk(90, 0.35)
    if name == "rumble":
        d = 2.0
        t = _t(d)
        return _lp_fast(_noise(d, 32), 160) * 3 * np.minimum(1, t / 0.15) * np.exp(-t / (d * 0.45))
    if name == "crash":
        d = 1.3
        out = np.zeros(int(d * GEN_SR))
        rng = np.random.default_rng(33)
        for _ in range(14):
            i = int(rng.uniform(0, d * 0.6) * GEN_SR)
            g = _thunk(rng.uniform(60, 160), 0.35, int(rng.integers(1, 999))) * rng.uniform(0.3, 0.9)
            out[i:i + len(g)] += g[: len(out) - i]
        return out + _lp_fast(_noise(d, 34), 2500) * np.exp(-_t(d) * 3) * 0.25
    if name == "scrape":
        d = 0.8
        t = _t(d)
        s = _noise(d, 35) * (0.5 + 0.5 * np.sin(2 * np.pi * 13 * t)) * np.sin(np.pi * t / d)
        return _hp_fast(_lp_fast(s, 5000), 1500) * 0.6 + np.sin(2 * np.pi * 1870 * t) * np.exp(-t * 3) * 0.2
    if name == "ting":
        t = _t(1.2)
        return sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in ((2093, 4), (3136, 6), (4186, 8))) * 0.3
    if name in ("sting", "sting_low"):
        d = 2.0
        t = _t(d)
        s = np.sin(2 * np.pi * 41 * t) * np.exp(-t * 1.5) * 1.2 + _lp_fast(_noise(d, 36), 900) * np.exp(-t * 6) * 0.8
        if name == "sting":
            stab = _brass([_midi(45), _midi(48), _midi(51)], 1.4)
            s[: len(stab)] += stab * 2.2 * np.exp(-np.arange(len(stab)) / GEN_SR * 2)
        return s
    if name == "creak":
        d = 0.6
        t = _t(d)
        rate = 140 * (1 + 0.35 * np.sin(2 * np.pi * 1.3 * t / d))
        pulses = (np.mod(np.cumsum(rate) / GEN_SR, 1) < 0.08).astype(float)
        rng = np.random.default_rng(37)
        return _hp_fast(_lp_fast(pulses * (0.6 + 0.4 * rng.random(len(t))), 2200) * np.sin(np.pi * t / d), 200) * 2.5
    if name == "snap":
        d = 0.5
        t = _t(d)
        th = np.zeros(len(t))
        g = _thunk(120, 0.4)
        th[: len(g)] = g
        return _hp_fast(_noise(d, 38), 800) * np.exp(-t * 18) * 1.4 + th * 0.6
    if name == "splash":
        d = 1.0
        t = _t(d)
        return (_lp_fast(_noise(d, 39), 4000) * np.exp(-t * 4) * np.minimum(1, t / 0.01)
                + _lp_fast(_noise(d, 40), 400) * np.exp(-t * 7) * 1.5)
    if name == "sizzle":
        d = 1.4
        t = _t(d)
        crackle = (np.random.default_rng(41).random(len(t)) > 0.9965).astype(float)
        crackle = _hp_fast(crackle, 2500) * 3
        hiss = _hp_fast(_lp_fast(_noise(d, 42), 9000), 3000)
        return (hiss * 0.7 + crackle) * np.minimum(1, t / 0.02) * np.exp(-t * 1.6)
    if name == "bubbles":
        d = 1.5
        out = np.zeros(int(d * GEN_SR))
        rng = np.random.default_rng(43)
        for _ in range(26):
            i = int(rng.uniform(0, d - 0.08) * GEN_SR)
            n = int(0.06 * GEN_SR)
            tt = np.arange(n) / GEN_SR
            f0 = rng.uniform(300, 900)
            seg = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2.5 * tt / 0.06)) / GEN_SR) * np.exp(-tt * 60) * rng.uniform(.3, .8)
            out[i:i + n] += seg[: len(out) - i]
        return out
    raise KeyError(name)


def _write(path, mono):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mono = mono / (np.abs(mono).max() + 1e-9) * 0.95
    data = (np.stack([mono, mono], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(GEN_SR)
        w.writeframes(data.tobytes())


def decode(path, sr=None, start=0.0, dur=None, mono=False):
    """File âm thanh/video → float32 (N, 2) hoặc (N,) ở sample rate pipeline. Rỗng nếu không có tiếng."""
    sr = sr or channel()["audio"]["sample_rate"]
    cmd = [ffbin("ffmpeg"), "-v", "error", "-ss", f"{start:.3f}", "-i", path]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-vn", "-ac", "1" if mono else "2", "-ar", str(sr), "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.float32).copy()
    return a if mono else a[: len(a) // 2 * 2].reshape(-1, 2)


def available():
    names = set(DESCRIPTIONS)
    if os.path.isdir(SFX_DIR):
        for f in os.listdir(SFX_DIR):
            base, ext = os.path.splitext(f)
            if ext.lower() in (".wav", ".mp3", ".ogg", ".m4a", ".flac"):
                names.add(base)
    return sorted(names)


def path_of(name):
    base, arg = split_name(name)
    if base in PARAM_SFX:
        p = os.path.join(BUILTIN_DIR, f"{base}_{arg or 0.5:.1f}.wav")
        if not os.path.exists(p):
            _write(p, _make_param(base, arg))
        return p
    for ext in (".wav", ".mp3", ".ogg", ".m4a", ".flac"):
        p = os.path.join(SFX_DIR, name + ext)
        if os.path.exists(p):
            return p
    if name not in DESCRIPTIONS:
        raise StudioError(f"Không có SFX '{name}'. Thêm assets/sfx/{name}.wav hoặc dùng: {', '.join(available())}.")
    p = os.path.join(BUILTIN_DIR, name + ".wav")
    if not os.path.exists(p):
        _write(p, _make(name))
    return p


_CACHE = {}


def load(name, sr=None):
    """Mảng float32 (N, 2), chuẩn hoá đỉnh = 1.0 (mức thật do audio.mix đặt theo dB)."""
    key = (name, sr)
    if key not in _CACHE:
        a = decode(path_of(name), sr)
        peak = float(np.abs(a).max()) if len(a) else 0.0
        _CACHE[key] = a / peak if peak > 0 else a
    return _CACHE[key]


def level_db(name):
    db = channel()["audio"]["sfx_db"]
    base, _ = split_name(name)
    return db.get(name, db.get(base, db.get("default", -10)))
