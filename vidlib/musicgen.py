"""Nhạc nền tổng hợp bằng code khi dự án không có audio/music.* (ý tưởng từ cartoon-short-kit/example/soldier/audio.py).

Vòng lặp ngắn kiểu "phòng thí nghiệm": kick/snare nhẹ, bass pluck, pad đồng; DỪNG ở câu twist (preset payoff) rồi
chỉ còn drone trầm tới hết. Xác định hoàn toàn (seed cố định) → render lại giống hệt.
"""
import numpy as np

SR = 48000


def _lp(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def _hp(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 - 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


def _midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def _pluck(f, dur=0.35, bright=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum((bright ** k) * np.sin(2 * np.pi * f * (k + 1) * t) / (k + 1) for k in range(6))
    return (s * _env(n, 0.003, dur * 0.35)).astype(np.float32)


def _pad(fs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f in fs:
        ph = 2 * np.pi * f * t + 0.003 * np.sin(2 * np.pi * 5 * t)
        s += sum(np.sin((k + 1) * ph) / (k + 1) ** 1.6 for k in range(6))
    a = np.minimum(1, t / 0.12) * np.clip(np.minimum(1, (dur - t) / 0.2), 0, 1)
    return _lp((s * a).astype(np.float32), 1400) / len(fs)


def _drum(kind, rng):
    if kind == "kick":
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        f = 50 + 90 * np.exp(-t * 30)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32)
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    s = rng.standard_normal(n) * np.exp(-t * 30) * 0.5 + np.sin(2 * np.pi * 200 * t) * np.exp(-t * 22) * 0.4
    return _hp(s.astype(np.float32), 400)


def bed(duration, stop_at=None, bpm=112, seed=7):
    """Mảng float32 (N, 2). stop_at (giây): nhạc tắt gọn ở đó, sau đó là drone trầm."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR // 10
    out = np.zeros(n, np.float32)
    end = min(duration, stop_at) if stop_at else duration

    def place(sig, t0, g):
        i = int(t0 * SR)
        j = min(n, i + len(sig))
        if i < n and j > i:
            out[i:j] += sig[: j - i] * g

    beat = 60 / bpm
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (55, [55, 59, 62]), (52, [52, 56, 59])]  # Am F G E
    bar, tt = 0, 0.0
    while tt < end:
        root, ch = prog[bar % 4]
        place(_pad([_midi(m) for m in ch], beat * 4 * 0.98), tt, 0.08)
        for b in range(4):
            tb = tt + b * beat
            if tb >= end:
                break
            place(_drum("kick" if b % 2 == 0 else "snare", rng), tb, 0.5 if b % 2 == 0 else 0.25)
            place(_pluck(_midi(root - 12), 0.4, 0.4), tb, 0.32)
            place(_pluck(_midi(ch[(b + bar) % 3] + 12), 0.2, 0.6), tb + beat / 2, 0.11)
        bar += 1
        tt += beat * 4
    if stop_at and stop_at < duration:
        i0 = int(max(0.0, stop_at - 0.06) * SR)
        out[i0:] *= np.linspace(1, 0, n - i0) ** 8
        dn = n - int(stop_at * SR)
        td = np.arange(dn) / SR
        drone = (np.sin(2 * np.pi * 55 * td) + 0.5 * np.sin(2 * np.pi * 82.4 * td) + 0.3 * np.sin(2 * np.pi * 110 * td))
        drone = _lp((drone * np.minimum(1, td / 1.0)).astype(np.float32), 600)
        place(drone, stop_at, 0.08)
    fade = int(0.5 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    return np.stack([out, out], 1)
