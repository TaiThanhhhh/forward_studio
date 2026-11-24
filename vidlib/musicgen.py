"""Nhạc nền tổng hợp bằng code khi dự án không có audio/music.* (Vòng 13: 5 bản sắc điện ảnh + đường cong năng lượng).

5 mood riêng biệt (tất định 100% theo seed, pure numpy float32 stereo (N, 2)):
- investigative_pulse (LEMMiNO / Fern): sub pulse D-minor 1/8 sâu tối, pad lọc mở dần, low click tinh tế.
- kinetic_editorial (Vox / Cleo Abram): marimba/plucked synth sáng sắc nét, trống biên tập gọn chắc.
- visceral_thriller (Zack D. Films): sub-drone u ám + kick nhịp tim đôi + ping kim loại cao thưa lạnh.
- clockwork_tension (Fern / Kurzgesagt): tích-tắc đồng hồ khoá BPM + tầng hòa âm dâng căng thẳng theo từng ô nhịp.
- minimal_cinematic (Johnny Harris / Ordinary Folk): hợp âm bell/electric-piano ấm áp + pad thoáng giữa cho VO.

Hỗ trợ Dramatic Dead-Air Drop (~0.35s lặng sắc trước stop_at rồi thả drone trầm sâu) và cue_times
({escalate_at, payoff_at, twist_at}) để mở bộ lọc và tăng mật độ nhạc cụ theo mạch cảm xúc.
"""
import numpy as np

SR = 48000

MOODS = (
    "investigative_pulse",
    "kinetic_editorial",
    "visceral_thriller",
    "clockwork_tension",
    "minimal_cinematic",
)


def _lp(x, cutoff):
    if len(x) == 0:
        return x.astype(np.float32)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / max(cutoff, 20.0)) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def _hp(x, cutoff):
    if len(x) == 0:
        return x.astype(np.float32)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 - 1 / (1 + (f / max(cutoff, 10.0)) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def _bp(x, lo, hi):
    return _hp(_lp(x, hi), lo)


def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))


def _midi(m):
    return 440.0 * 2.0 ** ((m - 69.0) / 12.0)


def _pluck(f, dur=0.35, bright=0.5):
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    s = sum((bright ** k) * np.sin(2 * np.pi * f * (k + 1) * t) / (k + 1) for k in range(6))
    return (s * _env(n, 0.003, dur * 0.35)).astype(np.float32)


def _pad(fs, dur, cutoff=1400.0):
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    s = np.zeros(n, dtype=np.float64)
    for idx, f in enumerate(fs):
        det = 1.0 + (idx - (len(fs) - 1) / 2.0) * 0.0014
        ph = 2 * np.pi * f * det * t + 0.003 * np.sin(2 * np.pi * (4.3 + idx * 0.3) * t)
        s += sum(np.sin((k + 1) * ph) / (k + 1) ** 1.65 for k in range(6))
    a = np.minimum(1.0, t / 0.14) * np.clip(np.minimum(1.0, (dur - t) / 0.22), 0.0, 1.0)
    return _lp((s * a).astype(np.float32), cutoff) / max(len(fs), 1)


def _drum(kind, rng):
    if kind == "kick":
        n = int(0.32 * SR)
        t = np.arange(n) / SR
        f = 48.0 + 95.0 * np.exp(-t * 34.0)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10.0)
        click = np.sin(2 * np.pi * 1600.0 * t) * np.exp(-t * 140.0) * 0.12
        return (body + click).astype(np.float32)
    if kind == "rim":
        n = int(0.11 * SR)
        t = np.arange(n) / SR
        s = (
            rng.standard_normal(n) * np.exp(-t * 55.0) * 0.45
            + np.sin(2 * np.pi * 420.0 * t) * np.exp(-t * 48.0) * 0.55
            + np.sin(2 * np.pi * 1680.0 * t) * np.exp(-t * 95.0) * 0.30
        )
        return _hp(s.astype(np.float32), 260.0)
    if kind == "hat":
        n = int(0.055 * SR)
        t = np.arange(n) / SR
        return _hp((rng.standard_normal(n) * np.exp(-t * 95.0)).astype(np.float32), 6200.0) * 0.35
    if kind == "low_click":
        n = int(0.065 * SR)
        t = np.arange(n) / SR
        s = (
            np.sin(2 * np.pi * 195.0 * t) * np.exp(-t * 68.0) * 0.65
            + rng.standard_normal(n) * np.exp(-t * 120.0) * 0.25
        )
        return _bp(s.astype(np.float32), 140.0, 950.0)
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    s = rng.standard_normal(n) * np.exp(-t * 30) * 0.5 + np.sin(2 * np.pi * 200 * t) * np.exp(-t * 22) * 0.4
    return _hp(s.astype(np.float32), 400)


def _sub_pulse(f, dur, cutoff=520.0):
    """Dark pulsing synth bass (saw + sub sine, low-passed) for investigative_pulse."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * f * t) * 0.80
    saw = sum(np.sin(2 * np.pi * f * (k + 1) * t) / (k + 1) for k in range(1, 6)) * 0.42
    env = np.minimum(1.0, t / 0.008) * np.exp(-t / max(dur * 0.55, 0.04))
    env *= np.clip((dur - t) / 0.015, 0.0, 1.0)
    return _lp(((sub + saw) * env).astype(np.float32), cutoff)


def _marimba(f, dur=0.28, bright=0.62):
    """Woody modern marimba / editorial pluck (fundamental + 4th harmonic resonance)."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    fund = np.sin(2 * np.pi * f * t) * np.exp(-t / max(dur * 0.36, 0.03))
    over1 = np.sin(2 * np.pi * (f * 3.98) * t) * np.exp(-t / max(dur * 0.09, 0.01)) * (0.34 * bright)
    over2 = np.sin(2 * np.pi * (f * 2.0) * t) * np.exp(-t / max(dur * 0.16, 0.015)) * (0.18 * bright)
    att = np.minimum(1.0, t / 0.0025)
    return ((fund + over1 + over2) * att).astype(np.float32)


def _heartbeat_kick(accent=1.0):
    """Deep visceral heartbeat sub-thump for visceral_thriller."""
    n = int(0.28 * SR)
    t = np.arange(n) / SR
    f = 34.0 + 48.0 * np.exp(-t * 24.0)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1.0, t / 0.007) * np.exp(-t * 11.5)
    return _lp((sig * accent).astype(np.float32), 180.0)


def _metal_ping(f, dur=1.15):
    """Sparse cold metallic high tension ping (inharmonic bell partials)."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    s = (
        np.sin(2 * np.pi * f * t) * np.exp(-t * 2.8) * 0.55
        + np.sin(2 * np.pi * (f * 2.756) * t) * np.exp(-t * 5.2) * 0.28
        + np.sin(2 * np.pi * (f * 4.07) * t) * np.exp(-t * 8.5) * 0.14
    )
    att = np.minimum(1.0, t / 0.003)
    return _hp((s * att).astype(np.float32), 900.0)


def _clock_tick(high, rng):
    """Crisp BPM-locked escapement clock tick / tock for clockwork_tension."""
    n = int(0.042 * SR)
    t = np.arange(n) / SR
    f0 = 3850.0 if high else 2550.0
    f1 = 5600.0 if high else 3620.0
    body = (
        np.sin(2 * np.pi * f0 * t) * 0.60
        + np.sin(2 * np.pi * f1 * t) * 0.35
        + rng.standard_normal(n) * 0.30
    ) * np.exp(-t * 175.0)
    return _bp(body.astype(np.float32), 1400.0, 8200.0)


def _epiano_chord(fs, dur, warmth=1.0):
    """Warm Rhodes-like electric piano bell chord for minimal_cinematic."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    s = np.zeros(n, dtype=np.float64)
    for idx, f in enumerate(fs):
        det = 1.0 + (idx - (len(fs) - 1) / 2.0) * 0.0009
        ff = f * det
        body = (
            np.sin(2 * np.pi * ff * t) * np.exp(-t / max(dur * 0.65, 0.25)) * 0.78
            + np.sin(2 * np.pi * (ff * 2.0) * t) * np.exp(-t / max(dur * 0.32, 0.12)) * 0.20
            + np.sin(2 * np.pi * (ff * 3.0) * t) * np.exp(-t / max(dur * 0.14, 0.06)) * 0.08
        )
        tine = np.sin(2 * np.pi * (ff * 6.0) * t) * np.exp(-t * 36.0) * 0.07
        s += body + tine
    env = np.minimum(1.0, t / 0.012) * np.clip((dur - t) / 0.14, 0.0, 1.0)
    return _lp(((s * env) / max(len(fs), 1)).astype(np.float32), 2100.0 * warmth)


def _energy_at(t, duration, cue_times):
    """Return (energy in [0.45, 1.0], phase) for dynamic tension progression."""
    dur = max(float(duration), 1.0)
    ct = cue_times if isinstance(cue_times, dict) else {}
    esc = ct.get("escalate_at")
    pay = ct.get("payoff_at")
    tw = ct.get("twist_at")

    if esc is None:
        esc = dur * 0.32
    if pay is None:
        pay = (tw - 3.0) if (tw is not None and tw > esc + 2.5) else dur * 0.72
    pay = max(float(pay), float(esc) + 0.5)
    hook_end = min(2.4, float(esc))

    if t < hook_end:
        return 0.68, "hook"
    if t < float(esc):
        u = (t - hook_end) / max(float(esc) - hook_end, 0.5)
        return 0.54 + 0.14 * np.clip(u, 0.0, 1.0), "setup"
    if t < pay:
        u = (t - float(esc)) / max(pay - float(esc), 0.5)
        return 0.72 + 0.24 * np.clip(u, 0.0, 1.0), "escalate"
    return 1.0, "payoff"


def _place_stereo(out, sig, t0, gain, pan=0.0):
    """Accumulate mono signal into stereo buffer (N, 2) with constant-power pan in [-1, 1]."""
    n = len(out)
    i = int(round(t0 * SR))
    if i >= n:
        return
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(n, i + len(sig))
    if j <= i:
        return
    seg = sig[: j - i]
    ang = (np.clip(pan, -1.0, 1.0) + 1.0) * (np.pi / 4.0)
    out[i:j, 0] += seg * (gain * float(np.cos(ang)))
    out[i:j, 1] += seg * (gain * float(np.sin(ang)))


def _drone_root_hz(mood):
    """Tonic sub-drone fundamental matching each mood's musical key."""
    return {
        "investigative_pulse": _midi(38),   # D2 (73.4 Hz) -> sub octave 36.7 Hz
        "kinetic_editorial": _midi(45),     # A2 (110 Hz) -> sub 55 Hz
        "visceral_thriller": _midi(36),     # C2 (65.4 Hz) -> sub 32.7 Hz
        "clockwork_tension": _midi(40),     # E2 (82.4 Hz) -> sub 41.2 Hz
        "minimal_cinematic": _midi(41),     # F2 (87.3 Hz) -> sub 43.65 Hz
    }.get(mood, 55.0)


def _render_investigative_pulse(out, end, beat, duration, cue_times, rng):
    """LEMMiNO / Fern: deep D-minor 1/8 pulsing sub bass, dark filtered pad, subtle low click."""
    prog = [
        (50, [50, 53, 57, 62]),  # Dm
        (46, [46, 50, 53, 57]),  # Bbmaj7
        (43, [43, 46, 50, 55]),  # Gm
        (45, [45, 50, 52, 57]),  # Asus4
    ]
    bar, tt = 0, 0.0
    while tt < end:
        energy, phase = _energy_at(tt, duration, cue_times)
        root, ch = prog[bar % 4]
        pad_cut = 580.0 + 620.0 * energy
        pad_sig = _pad([_midi(m) for m in ch], beat * 4 * 0.99, cutoff=pad_cut)
        _place_stereo(out, pad_sig, tt, 0.11 + 0.06 * energy, pan=-0.12 if bar % 2 == 0 else 0.12)

        sub_cut = 300.0 + 420.0 * energy
        for s in range(8):
            ts = tt + s * (beat / 2.0)
            if ts >= end:
                break
            accent = 1.0 if s % 2 == 0 else (0.64 + 0.18 * energy)
            note = root - 12 if s != 7 else root - 12 + (2 if bar % 2 == 0 else 0)
            _place_stereo(out, _sub_pulse(_midi(note), beat * 0.46, cutoff=sub_cut), ts, 0.34 * accent, pan=0.0)
            if s in (2, 6):
                _place_stereo(out, _drum("low_click", rng), ts, 0.16 + 0.08 * energy, pan=0.18 if s == 2 else -0.18)
            if phase in ("escalate", "payoff") and s in (1, 3, 5, 7):
                arp_m = ch[(s // 2 + bar) % len(ch)] + 12
                arp = _lp(_pluck(_midi(arp_m), beat * 0.42, bright=0.35 + 0.2 * energy), 1500.0)
                _place_stereo(out, arp, ts, 0.075 * energy, pan=-0.28 if s % 4 == 1 else 0.28)
        bar += 1
        tt += beat * 4.0


def _render_kinetic_editorial(out, end, beat, duration, cue_times, rng):
    """Vox / Cleo Abram: crisp modern marimba/plucked synth progression + tight punchy percussion."""
    prog = [
        (57, [57, 60, 64, 67]),  # Am7
        (53, [53, 57, 60, 64]),  # Fmaj7
        (48, [48, 52, 55, 59]),  # Cmaj7
        (55, [55, 59, 62, 64]),  # G6
    ]
    bar, tt = 0, 0.0
    while tt < end:
        energy, phase = _energy_at(tt, duration, cue_times)
        root, ch = prog[bar % 4]
        pad_sig = _pad([_midi(m) for m in ch[:3]], beat * 4 * 0.96, cutoff=1100.0 + 500.0 * energy)
        _place_stereo(out, pad_sig, tt, 0.055 + 0.03 * energy, pan=0.0)

        for b in range(4):
            tb = tt + b * beat
            if tb >= end:
                break
            if b in (0, 2):
                _place_stereo(out, _drum("kick", rng), tb, 0.42 + 0.08 * energy, pan=0.0)
            else:
                _place_stereo(out, _drum("rim", rng), tb, 0.24 + 0.08 * energy, pan=0.08)

            bass_m = root - 12 if root >= 52 else root
            _place_stereo(out, _pluck(_midi(bass_m), beat * 0.65, bright=0.35 + 0.15 * energy), tb, 0.28, pan=0.0)

            # Crisp syncopated marimba motif
            m1 = ch[(b + bar) % len(ch)] + 12
            sig1 = _marimba(_midi(m1), beat * 0.48, bright=0.55 + 0.35 * energy)
            _place_stereo(out, sig1, tb, 0.18 + 0.06 * energy, pan=-0.22)
            t_off = tb + beat * 0.5
            if t_off < end:
                m2 = ch[(b + 2) % len(ch)] + 12
                sig2 = _marimba(_midi(m2), beat * 0.36, bright=0.65 + 0.3 * energy)
                _place_stereo(out, sig2, t_off, 0.14 + 0.07 * energy, pan=0.25)
                if phase in ("escalate", "payoff"):
                    _place_stereo(out, _drum("hat", rng), t_off, 0.16 * energy, pan=0.32 if b % 2 == 0 else -0.32)
            if phase == "payoff" and tb + beat * 0.75 < end:
                m3 = ch[(b + 1) % len(ch)] + 24
                _place_stereo(out, _marimba(_midi(m3), beat * 0.25, bright=0.8), tb + beat * 0.75, 0.09, pan=-0.3)
        bar += 1
        tt += beat * 4.0


def _render_visceral_thriller(out, end, beat, duration, cue_times, rng):
    """Zack D. Films: low ominous sub-drone + heartbeat double-thump kick + sparse metallic high ping."""
    # Continuous ominous sub-drone across the active bed
    dn = min(len(out), max(1, int(end * SR)))
    td = np.arange(dn) / SR
    lfo = 0.78 + 0.22 * np.sin(2 * np.pi * 0.38 * td)
    f_sub = _midi(36) / 2.0  # C1 ~32.7 Hz
    drone = (
        np.sin(2 * np.pi * f_sub * td) * 0.65
        + np.sin(2 * np.pi * (f_sub * 2.0) * td) * 0.42
        + np.sin(2 * np.pi * (f_sub * 3.0) * td + 0.3 * np.sin(2 * np.pi * 0.2 * td)) * 0.14
    ) * lfo * np.minimum(1.0, td / 0.45)
    drone = _lp(drone.astype(np.float32), 210.0)
    _place_stereo(out, drone, 0.0, 0.24, pan=0.0)

    # Phrygian tension roots (C, Db, C, B) for ominous dark swells & metallic pings
    ping_notes = [84, 85, 91, 83]  # C6, Db6, G6, B5
    bar, tt = 0, 0.0
    while tt < end:
        energy, phase = _energy_at(tt, duration, cue_times)
        # Heartbeat double-thump: once per 2 beats in hook/setup, every 2 beats stronger + extra tension in escalate/payoff
        step_beats = 2 if phase in ("escalate", "payoff") else 4
        for b in range(0, 4, step_beats):
            tb = tt + b * beat
            if tb >= end:
                break
            _place_stereo(out, _heartbeat_kick(1.0), tb, 0.56 + 0.14 * energy, pan=0.0)
            t2 = tb + min(0.26, beat * 0.42)
            if t2 < end:
                _place_stereo(out, _heartbeat_kick(0.76), t2, 0.44 + 0.12 * energy, pan=0.0)

        # Sparse cold metallic high tension ping
        ping_t = tt + (beat * 1.5 if bar % 2 == 0 else beat * 2.5)
        if ping_t < end and (bar % 2 == 0 or phase in ("escalate", "payoff")):
            pf = _midi(ping_notes[bar % len(ping_notes)])
            pan = -0.38 if bar % 2 == 0 else 0.38
            _place_stereo(out, _metal_ping(pf, dur=1.25), ping_t, 0.075 + 0.055 * energy, pan=pan)

        # Dark eerie tension swell during escalate / payoff
        if phase in ("escalate", "payoff"):
            chord = [48, 49, 55] if bar % 2 == 1 else [48, 55, 56]
            swell = _pad([_midi(m) for m in chord], beat * 4 * 0.95, cutoff=420.0 + 380.0 * energy)
            _place_stereo(out, swell, tt, 0.08 * energy, pan=0.0)

        bar += 1
        tt += beat * 4.0


def _render_clockwork_tension(out, end, beat, duration, cue_times, rng):
    """Fern / Kurzgesagt: BPM-locked crisp clock ticks + rising harmonic tension layers across bars."""
    prog = [
        (52, [52, 55, 59, 64]),  # Em
        (48, [48, 52, 55, 62]),  # Cadd9
        (50, [50, 54, 57, 64]),  # Dadd9
        (47, [47, 51, 54, 59]),  # B
    ]
    total_bars = max(1.0, end / (beat * 4.0))
    bar, tt = 0, 0.0
    while tt < end:
        energy, phase = _energy_at(tt, duration, cue_times)
        bar_ramp = min(1.0, (bar + 1) / total_bars)
        intensity = 0.45 * energy + 0.55 * bar_ramp
        root, ch = prog[bar % 4]

        # Rising harmonic tension pad (cutoff & level climb steadily across bars)
        pad_cut = 520.0 + 1750.0 * intensity
        pad_sig = _pad([_midi(m) for m in ch], beat * 4 * 0.98, cutoff=pad_cut)
        _place_stereo(out, pad_sig, tt, 0.06 + 0.13 * intensity, pan=0.0)

        # Upper tension octave layer joins as bars progress
        if intensity > 0.45:
            hi_pad = _pad([_midi(m + 12) for m in ch[:2]], beat * 4 * 0.98, cutoff=900.0 + 1600.0 * intensity)
            _place_stereo(out, hi_pad, tt, 0.085 * (intensity - 0.35), pan=-0.16 if bar % 2 == 0 else 0.16)

        # Crisp BPM-locked clock ticks on every 1/8 note (+ 1/16 double-ticks in payoff)
        sub_div = 16 if phase == "payoff" else 8
        step = (beat * 4.0) / sub_div
        for s in range(sub_div):
            ts = tt + s * step
            if ts >= end:
                break
            high = (s % 2 == 0)
            g_tick = (0.24 if high else 0.15) * (0.8 + 0.35 * intensity)
            _place_stereo(out, _clock_tick(high, rng), ts, g_tick, pan=-0.24 if high else 0.24)

        # Tight mechanical bass/ostinato pulse on beats
        for b in range(4):
            tb = tt + b * beat
            if tb >= end:
                break
            if b == 0 or (phase in ("escalate", "payoff") and b == 2):
                _place_stereo(out, _drum("kick", rng), tb, 0.24 + 0.14 * intensity, pan=0.0)
            bass = _pluck(_midi(root - 12), beat * 0.42, bright=0.35 + 0.35 * intensity)
            _place_stereo(out, bass, tb, 0.22 + 0.08 * intensity, pan=0.0)
            ost_m = ch[(b + bar) % len(ch)] + 12
            ost = _pluck(_midi(ost_m), beat * 0.24, bright=0.5 + 0.4 * intensity)
            _place_stereo(out, ost, tb + beat * 0.5, 0.07 + 0.09 * intensity, pan=0.22 if b % 2 == 0 else -0.22)

        bar += 1
        tt += beat * 4.0


def _render_minimal_cinematic(out, end, beat, duration, cue_times, rng):
    """Johnny Harris / Ordinary Folk: warm electric-piano bell chords + gentle atmospheric swell, clean midrange."""
    prog = [
        (53, [53, 57, 60, 64]),  # Fmaj7
        (48, [48, 55, 59, 62]),  # Cmaj9
        (57, [57, 60, 64, 67]),  # Am7
        (55, [55, 59, 62, 64]),  # G6
    ]
    bar, tt = 0, 0.0
    while tt < end:
        energy, phase = _energy_at(tt, duration, cue_times)
        root, ch = prog[bar % 4]

        # Warm electric piano bell chord on beat 1 (and gentle re-articulation on beat 3 during escalate/payoff)
        ep = _epiano_chord([_midi(m) for m in ch], beat * 3.85, warmth=0.85 + 0.35 * energy)
        _place_stereo(out, ep, tt, 0.28 + 0.06 * energy, pan=-0.08 if bar % 2 == 0 else 0.08)

        # Gentle airy atmospheric swell
        pad_sig = _pad([_midi(m) for m in ch[:3]], beat * 4 * 0.99, cutoff=720.0 + 420.0 * energy)
        _place_stereo(out, pad_sig, tt, 0.085 + 0.045 * energy, pan=0.14 if bar % 2 == 0 else -0.14)

        # Warm clean sub-bass root (round sine, zero mud in midrange)
        bass_n = max(1, int(beat * 3.6 * SR))
        tb_arr = np.arange(bass_n) / SR
        f_root = _midi(root - 12 if root >= 52 else root)
        bass = np.sin(2 * np.pi * f_root * tb_arr) * np.minimum(1.0, tb_arr / 0.04) * np.exp(-tb_arr / (beat * 2.2))
        _place_stereo(out, bass.astype(np.float32), tt, 0.22, pan=0.0)

        # Delicate bell melody notes (open midrange, expressive)
        for step_b, deg, pan in ((1.5, 3, 0.24), (2.5, 2, -0.22), (3.5, 1, 0.18)):
            tn = tt + step_b * beat
            if tn >= end:
                break
            if step_b == 3.5 and phase in ("hook", "setup"):
                continue
            bell = _epiano_chord([_midi(ch[deg % len(ch)] + 12)], beat * 1.1, warmth=1.1)
            _place_stereo(out, bell, tn, 0.10 + 0.05 * energy, pan=pan)

        # Subtle soft pulse only in escalate/payoff (keeps track intimate and breathable)
        if phase in ("escalate", "payoff"):
            for b in (0, 2):
                tb = tt + b * beat
                if tb < end:
                    _place_stereo(out, _heartbeat_kick(0.55), tb, 0.18 * energy, pan=0.0)

        bar += 1
        tt += beat * 4.0


_RENDERERS = {
    "investigative_pulse": _render_investigative_pulse,
    "kinetic_editorial": _render_kinetic_editorial,
    "visceral_thriller": _render_visceral_thriller,
    "clockwork_tension": _render_clockwork_tension,
    "minimal_cinematic": _render_minimal_cinematic,
}


def bed(duration, stop_at=None, bpm=112, seed=7, mood="kinetic_editorial", cue_times=None):
    """Mảng float32 (N, 2).

    - mood: 1 trong MOODS (mặc định 'kinetic_editorial').
    - cue_times: dict tuỳ chọn {'escalate_at', 'payoff_at', 'twist_at'} để mở bộ lọc & năng lượng theo mạch truyện.
    - stop_at (giây): Dramatic Dead-Air Drop ~0.35s trước stop_at rồi thả drone trầm sâu hợp điệu tới hết.
    """
    mood_key = mood if mood in _RENDERERS else "kinetic_editorial"
    rng = np.random.default_rng(seed)
    n = max(1, int(duration * SR) + SR // 10)
    out = np.zeros((n, 2), np.float32)

    has_stop = stop_at is not None and 0.0 < float(stop_at) < float(duration)
    dead_air = min(0.35, float(stop_at) * 0.45) if has_stop else 0.0
    drop_at = max(0.0, float(stop_at) - dead_air) if has_stop else float(duration)
    end = min(float(duration), drop_at) if has_stop else float(duration)

    beat = 60.0 / max(float(bpm or 112), 40.0)
    _RENDERERS[mood_key](out, end, beat, duration, cue_times, rng)

    if has_stop:
        # Dramatic Dead-Air Drop: cut sharply ~0.35s before stop_at for crisp silence impact
        i_drop = min(n, int(round(drop_at * SR)))
        cut_len = min(int(0.045 * SR), max(1, n - i_drop))
        if i_drop < n:
            fade_drop = (np.linspace(1.0, 0.0, cut_len, dtype=np.float32) ** 4)[:, None]
            out[i_drop : i_drop + cut_len] *= fade_drop
            out[i_drop + cut_len :] = 0.0

        # Enter subtle deep key-matched drone tail cleanly at stop_at
        i_stop = min(n, int(round(float(stop_at) * SR)))
        dn = n - i_stop
        if dn > 0:
            td = np.arange(dn) / SR
            f0 = _drone_root_hz(mood_key)
            f_sub = f0 / 2.0 if f0 > 62.0 else f0
            drone_l = (
                np.sin(2 * np.pi * f_sub * td)
                + 0.48 * np.sin(2 * np.pi * (f_sub * 1.5) * td)
                + 0.24 * np.sin(2 * np.pi * (f_sub * 2.0) * td)
            )
            drone_r = (
                np.sin(2 * np.pi * (f_sub * 1.0015) * td)
                + 0.48 * np.sin(2 * np.pi * (f_sub * 1.501) * td)
                + 0.24 * np.sin(2 * np.pi * (f_sub * 1.999) * td)
            )
            env_d = np.minimum(1.0, td / 0.65)
            out[i_stop:, 0] += _lp((drone_l * env_d).astype(np.float32), 420.0) * 0.095
            out[i_stop:, 1] += _lp((drone_r * env_d).astype(np.float32), 420.0) * 0.095

    fade = min(int(0.5 * SR), n)
    if fade > 0:
        out[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]

    peak = float(np.abs(out).max())
    if peak > 0.90:
        out *= np.float32(0.90 / peak)
    return out.astype(np.float32)
