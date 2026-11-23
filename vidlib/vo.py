"""Lời đọc: tách câu, cắt lặng, tăng tốc, lấy mốc từng từ.

Luồng: audio/vo.* (một file) hoặc audio/vo_01.*, vo_02.* (mỗi câu một file)
  1. Tách câu: file đơn → N−1 khoảng lặng dài nhất (≥ line_gap_min_ms) làm ranh giới câu.
  2. Cắt lặng: khoảng lặng > max_silence_ms rút còn keep_silence_ms; trước câu payoff giữ pre_payoff_pause_ms.
     Lặng đầu file rút còn ~0.05s (VO phải bắt đầu trước frame 6).
  3. Tăng tốc: ffmpeg atempo (giữ cao độ).
  4. Mốc từng từ (vidlib/timing.py): timestamp ElevenLabs (audio/vo_alignment.json) → whisper → căn theo khoảng lặng
     (port timing.py của cartoon-short-kit, đã chuẩn hoá số trước khi đếm âm tiết). Chế độ cuối được IN RÕ ra màn hình.
"""
import os
import re
import tempfile

import numpy as np

from . import lang, timing, tts
from . import sfx as sfxlib
from .common import AUDIO_EXT, channel, find_file, run
from .fakes import write_wav

WIN = 0.01  # 10 ms


def vo_lines(sb):
    """[{text, shots:[idx…], beat}] — shot có 'vo' mở câu mới; shot không 'vo' minh hoạ tiếp câu trước."""
    lines = []
    for i, s in enumerate(sb["shots"]):
        if tts.strip_tags(s.get("vo", "")):
            lines.append({"text": tts.strip_tags(s["vo"]), "raw": s["vo"].strip(), "shots": [i], "beat": s.get("beat")})
        elif lines:
            lines[-1]["shots"].append(i)
    return lines


def find_vo(proj, n_lines):
    adir = os.path.join(proj, "audio")
    per = [find_file(adir, [f"vo_{k + 1:02d}", f"vo_{k + 1}"], AUDIO_EXT) for k in range(n_lines)]
    if n_lines and all(per):
        return "lines", per
    one = find_file(adir, ["vo", "voice", "voiceover"], AUDIO_EXT)
    return ("single", one) if one else (None, None)


def _rms_db(mono, sr):
    w = int(WIN * sr)
    m = len(mono) // w
    if m == 0:
        return np.zeros(0)
    rms = np.sqrt((mono[: m * w].reshape(m, w) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms / (rms.max() + 1e-12))


def silent_runs(mono, sr, db=-38.0):
    """Các đoạn lặng [(start_s, end_s)] (tính theo cửa sổ 10ms)."""
    lv = _rms_db(mono, sr)
    sil = lv < db
    runs, i, m = [], 0, len(sil)
    while i < m:
        if sil[i]:
            j = i
            while j < m and sil[j]:
                j += 1
            runs.append((i * WIN, j * WIN))
            i = j
        else:
            i += 1
    return runs


def split_lines(mono, sr, n, min_gap, weights=None):
    """Ranh giới câu: chọn n−1 khoảng lặng sao cho độ dài từng câu khớp nhất với số âm tiết của câu đó
    (giọng TTS thật hay ngừng ở dấu phẩy/hai chấm lâu hơn giữa câu → "lặng dài nhất" là chưa đủ).
    Quy hoạch động: chi phí = lệch vị trí so với kỳ vọng theo âm tiết − thưởng nhẹ cho khoảng lặng dài."""
    dur = len(mono) / sr
    runs = [r for r in silent_runs(mono, sr) if r[0] > 0.02 and r[1] < dur - 0.02 and r[1] - r[0] >= min_gap]
    if n <= 1:
        return [(0.0, dur)]
    if len(runs) < n - 1:
        return None
    w = np.asarray(weights if weights is not None else [1.0] * n, float)
    exp = np.cumsum(w)[:-1] / w.sum() * dur  # vị trí kỳ vọng của n−1 ranh giới
    mids = np.array([(a + b) / 2 for a, b in runs])
    lens = np.array([b - a for a, b in runs])
    bonus = 0.35 * lens / (lens.max() + 1e-9)  # giây
    m, k = len(runs), n - 1
    inf = float("inf")
    cost = np.full((k, m), inf)
    back = np.zeros((k, m), int)
    cost[0] = np.abs(mids - exp[0]) - bonus
    for j in range(1, k):
        best, arg = inf, -1
        for i in range(m):
            if i >= 1 and cost[j - 1, i - 1] < best:
                best, arg = cost[j - 1, i - 1], i - 1
            if arg >= 0:
                cost[j, i] = best + abs(mids[i] - exp[j]) - bonus[i]
                back[j, i] = arg
    i = int(np.argmin(cost[k - 1]))
    pick = [i]
    for j in range(k - 1, 0, -1):
        i = back[j, i]
        pick.append(i)
    pick.reverse()
    bounds = [0.0] + [float(mids[p]) for p in pick] + [dur]
    return list(zip(bounds, bounds[1:]))


def compress(mono, sr, max_sil, keep, keep_at=None, lead=0.05):
    """Rút các khoảng lặng dài. keep_at: {thời điểm gốc: độ dài giữ} cho khoảng lặng chứa thời điểm đó.
    Trả về (audio mới, hàm warp(t_gốc) → t_mới)."""
    keep_at = keep_at or {}
    dur = len(mono) / sr
    runs = silent_runs(mono, sr)
    cuts = []  # (orig_start, orig_end, new_len)
    for a, b in runs:
        want = keep
        for t0, k in keep_at.items():
            if a <= t0 <= b:
                want = max(want, k)
        if a <= 0.0001:  # lặng đầu file
            if b > lead:
                cuts.append((0.0, b, lead))
            continue
        if b >= dur - 0.0001:
            cuts.append((a, dur, min(b - a, 0.25)))
            continue
        if b - a > max_sil and b - a > want:
            cuts.append((a, b, want))
    pieces, xs, ys = [], [0.0], [0.0]
    pos, new = 0.0, 0.0
    for a, b, nl in cuts:
        pieces.append(mono[int(pos * sr):int(a * sr)])
        new += a - pos
        xs.append(a)
        ys.append(new)
        h = nl / 2
        pieces.append(mono[int(a * sr):int((a + h) * sr)])
        pieces.append(mono[int((b - h) * sr):int(b * sr)])
        new += nl
        xs.append(b)
        ys.append(new)
        pos = b
    pieces.append(mono[int(pos * sr):])
    new += dur - pos
    xs.append(dur)
    ys.append(new)
    out = np.concatenate([p for p in pieces if len(p)]) if pieces else mono
    xs_a, ys_a = np.array(xs), np.array(ys)
    return out.astype(np.float32), (lambda t: float(np.interp(t, xs_a, ys_a)))


def atempo(mono, sr, speed):
    if abs(speed - 1.0) < 1e-3:
        return mono
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        write_wav(src, np.stack([mono, mono], 1), sr)
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-filter:a", f"atempo={speed:.4f}", "-ac", "1", "-ar", str(sr), dst],
            "ffmpeg (atempo)")
        return sfxlib.decode(dst, sr, mono=True)


def _tokens(text):
    """Token hiển thị (giữ dấu câu dính từ) + trọng số âm tiết."""
    toks = [t for t in re.split(r"\s+", text.strip()) if t]
    return [(t, max(1, lang.syllables_spoken(t) or 1)) for t in toks]


def voiced_mask(mono, sr, db=-38.0):
    return _rms_db(mono, sr) >= db


def distribute(text, start, end, mask):
    """Chia token theo thời gian CÓ TIẾNG trong [start, end)."""
    toks = _tokens(text)
    if not toks:
        return []
    i0, i1 = int(start / WIN), max(int(start / WIN) + 1, int(end / WIN))
    seg = mask[i0:i1] if i1 <= len(mask) else np.concatenate([mask[i0:], np.ones(i1 - len(mask), bool)])
    if seg.sum() < 3:
        seg = np.ones(i1 - i0, bool)
    cum = np.cumsum(seg) / seg.sum()
    total = sum(w for _, w in toks)
    out, acc = [], 0
    for tok, w in toks:
        a, b = acc / total, (acc + w) / total
        ia = int(np.searchsorted(cum, a, side="right"))
        ib = int(np.searchsorted(cum, b - 1e-9, side="left"))
        out.append({"w": tok, "start": round(start + ia * WIN, 3), "end": round(start + (ib + 1) * WIN, 3)})
        acc += w
    return out


def _raw_words(proj, src, raw, sr, lines, log):
    """Mốc từ trên audio GỐC: ElevenLabs → whisper → căn theo khoảng lặng. Trả về (words, nguồn, ghi chú)."""
    notes = []
    al = tts.load_alignment(proj, src)
    if al:
        toks = [(k, t) for k, ln in enumerate(lines) for t in ln["text"].split()]
        aw = al.get("words") or []
        if len(aw) == len(toks) and all(a["w"] == t for a, (_, t) in zip(aw, toks)):
            return [dict(w, line=k) for w, (k, _) in zip(aw, toks)], "ElevenLabs timestamps", notes
        notes.append("vo_alignment.json không khớp lời hiện tại (đã sửa vo sau khi tạo giọng?) — bỏ qua.")
    ww, why = timing.whisper_words(raw, sr, write_wav)
    if ww:
        return timing.match_whisper(ww, lines), why, notes
    notes.append(f"whisper: {why}")
    dur = len(raw) / sr
    # như silencedetect d=0.12 của kit: lặng ngắn hơn 0.12s (giữa âm tiết) không phải ranh giới cụm
    runs = [r for r in silent_runs(raw, sr) if r[1] - r[0] >= 0.12]
    segs = timing.speech_segments(runs, dur)
    words, _, cost = timing.align(" ".join(ln["text"] for ln in lines), segs)
    log("  " + timing.SILENCE_NOTICE)
    notes.append(timing.SILENCE_NOTICE)
    if not words:  # DP không khớp nổi → tách câu theo lặng dài nhất + chia âm tiết trong vùng có tiếng
        split = split_lines(raw, sr, len(lines), channel()["vo"]["line_gap_min_ms"] / 1000,
                            weights=[max(1, lang.syllables_spoken(ln["text"])) for ln in lines]) \
            or [(dur * k / len(lines), dur * (k + 1) / len(lines)) for k in range(len(lines))]
        mask = voiced_mask(raw, sr)
        out = []
        for k, (ln, (a, b)) in enumerate(zip(lines, split)):
            out += [dict(w, line=k) for w in distribute(ln["text"], a, b, mask)]
        return out, "căn theo khoảng lặng (tách câu + chia âm tiết)", notes
    out = []
    for k, grp in enumerate(timing.assign_lines(words, lines)):
        out += [dict(w, line=k) for w in grp]
    return out, f"căn theo khoảng lặng (cost {cost:.2f})", notes


def process(proj, sb, sr=None, log=print):
    """Trả về dict {audio (N,2), duration, lines:[{text,start,end,shots,words}], source, timing, notes} hoặc None."""
    cfg = channel()["vo"]
    sr = sr or channel()["audio"]["sample_rate"]
    lines = vo_lines(sb)
    if not lines:
        return None
    kind, src = find_vo(proj, len(lines))
    if not kind:
        return None
    notes = []
    gap = cfg["keep_silence_ms"] / 1000
    pause = cfg["pre_payoff_pause_ms"] / 1000
    payoff_idx = next((k for k, ln in enumerate(lines) if ln["beat"] == "payoff"), None)
    words_by_line = None
    how = "chia theo vùng có tiếng"
    if kind == "lines":
        parts, bounds, t = [], [], 0.0
        for k, p in enumerate(src):
            a = sfxlib.decode(p, sr, mono=True)
            a, _ = compress(a, sr, cfg["max_silence_ms"] / 1000, gap, lead=0.0)
            if k:
                g = pause if k == payoff_idx else gap
                parts.append(np.zeros(int(g * sr), np.float32))
                t += g
            parts.append(a)
            bounds.append((t, t + len(a) / sr))
            t += len(a) / sr
        mono = np.concatenate(parts)
    else:
        raw = sfxlib.decode(src, sr, mono=True)
        words, how, n2 = _raw_words(proj, src, raw, sr, lines, log)
        notes += n2
        raw_bounds = []
        for k in range(len(lines)):
            ws = [w for w in words if w["line"] == k]
            raw_bounds.append((ws[0]["start"], ws[-1]["end"]) if ws else None)
        keep_at = {}
        if payoff_idx and raw_bounds[payoff_idx] and raw_bounds[payoff_idx - 1]:
            keep_at[(raw_bounds[payoff_idx - 1][1] + raw_bounds[payoff_idx][0]) / 2] = pause
        mono, warp = compress(raw, sr, cfg["max_silence_ms"] / 1000, gap, keep_at)
        words_by_line = [[{"w": w["w"], "start": warp(w["start"]), "end": warp(w["end"])}
                          for w in words if w["line"] == k] for k in range(len(lines))]
        bounds = [((ws[0]["start"], ws[-1]["end"]) if ws else (0.0, 0.0)) for ws in words_by_line]
    from .voices import tempo_for  # noqa: PLC0415 — mỗi video một giọng → atempo theo nhịp thật của giọng đó
    speed, why = tempo_for(proj, sb, float(cfg.get("speed") or 1.0))
    if why:
        notes.append(why)
    before = len(mono) / sr
    mono = atempo(mono, sr, speed)
    k = (len(mono) / sr) / max(before, 1e-6)
    bounds = [(a * k, b * k) for a, b in bounds]
    mask = voiced_mask(mono, sr)
    out_lines = []
    for i, (ln, (a, b)) in enumerate(zip(lines, bounds)):
        if words_by_line is not None and words_by_line[i]:
            ws = [{"w": w["w"], "start": round(w["start"] * k, 3), "end": round(w["end"] * k, 3)} for w in words_by_line[i]]
        else:  # file từng câu: bám vào vùng có tiếng rồi chia âm tiết
            i0, i1 = int(a / WIN), min(len(mask), int(b / WIN) + 1)
            idx = np.nonzero(mask[i0:i1])[0]
            if len(idx):
                a, b = a + idx[0] * WIN, a + (idx[-1] + 1) * WIN
            ws = distribute(ln["text"], a, b, mask)
        out_lines.append({"text": ln["text"], "shots": ln["shots"], "beat": ln["beat"], "start": round(ws[0]["start"], 3)
                          if ws else round(a, 3), "end": round(ws[-1]["end"], 3) if ws else round(b, 3), "words": ws})
    notes.append(f"Mốc từ: {how}")
    stereo = np.stack([mono, mono], 1).astype(np.float32)
    return {"audio": stereo, "sr": sr, "duration": len(mono) / sr, "lines": out_lines, "source": kind,
            "speed": speed, "timing": how, "notes": notes}
