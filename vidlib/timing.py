"""Mốc từng từ của lời đọc — thứ tự ưu tiên:

1. Timestamp ElevenLabs (audio/vo_alignment.json, tts.py) — chính xác tới ký tự.
2. faster-whisper / openai-whisper (nếu cài và tải được model).
3. Căn theo khoảng lặng (port tools/timing.py của cartoon-short-kit): tách cụm theo dấu câu, quy hoạch động khớp
   số âm tiết với độ dài từng đoạn có tiếng. Đã sửa lỗ hổng của kit:
   - số và ký hiệu đổi sang chữ TRƯỚC khi đếm âm tiết ("1,000°C" = 'one thousand degrees Celsius' = 7 âm tiết,
     kit cũ đếm thành 2);
   - không tải được model whisper (mạng chặn…) thì IN RÕ là đang chạy chế độ căn theo khoảng lặng.
"""
import functools
import os
import re
import tempfile

import numpy as np

from . import lang

SILENCE_NOTICE = ("⚠ KHÔNG có timestamp ElevenLabs/whisper → đang chạy chế độ CĂN THEO KHOẢNG LẶNG "
                  "(sai số ~1–3 frame mỗi từ). Nên tạo VO bằng ElevenLabs (có timestamp) hoặc cài faster-whisper.")


def whisper_words(mono, sr, write_wav):
    """(words, ghi chú). words=None nếu không dùng được whisper — ghi chú nói lý do."""
    model_name = os.environ.get("WHISPER_MODEL", "small.en" if lang.language() == "en" else "small")
    try:
        from faster_whisper import WhisperModel  # noqa: PLC0415
    except ImportError:
        WhisperModel = None
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "vo.wav")
        write_wav(p, np.stack([mono, mono], 1), sr)
        if WhisperModel is not None:
            try:
                model = WhisperModel(model_name, compute_type="int8")
                segs, _ = model.transcribe(p, language=lang.language()[:2], word_timestamps=True)
                return [{"w": w.word.strip(), "start": w.start, "end": w.end} for s in segs for w in s.words], \
                    f"faster-whisper ({model_name})"
            except Exception as ex:  # noqa: BLE001 — thường là không tải được model (mạng chặn)
                return None, f"faster-whisper có cài nhưng không chạy được ({type(ex).__name__}: {str(ex)[:120]})"
        try:
            import whisper  # noqa: PLC0415
        except ImportError:
            return None, "chưa cài faster-whisper / openai-whisper"
        try:
            r = whisper.load_model(model_name).transcribe(p, word_timestamps=True, language=lang.language()[:2])
            return [{"w": w["word"].strip(), "start": w["start"], "end": w["end"]}
                    for s in r["segments"] for w in s["words"]], f"openai-whisper ({model_name})"
        except Exception as ex:  # noqa: BLE001
            return None, f"openai-whisper không tải được model ({type(ex).__name__}: {str(ex)[:120]})"


def phrases_of(script):
    """Tách cụm sau , . ; : ! ? (giữ dấu). Không tách dấu phẩy/chấm NẰM TRONG số ("1,000", "2.5")."""
    raw = re.findall(r"(?:[^,.;:!?]|(?<=\d)[,.](?=\d))+[,.;:!?\"”']*", script.replace("\n", " "))
    return [p.strip() for p in raw if p.strip()]


def phrase_syllables(p):
    return max(1, lang.syllables_spoken(p))


def align(script, segs):
    """Căn cụm vào đoạn có tiếng (port nguyên DP của kit, đếm âm tiết đã chuẩn hoá số).
    Trả về (words [{w, start, end}], phrases [{text, start, end}], cost)."""
    phrases = phrases_of(script)
    P, S = len(phrases), len(segs)
    if not P or not S:
        return [], [], float("inf")
    syl = [phrase_syllables(p) for p in phrases]
    rate = sum(syl) / max(sum(e - s for s, e in segs), 1e-6)
    INF = 1e9

    @functools.lru_cache(None)
    def best(i, j):
        if i == P and j == S:
            return 0.0, ()
        if i == P or j == S:
            return INF, ()
        out = (INF, ())
        for k in range(i + 1, min(P, i + 4) + 1):
            for m in range(j + 1, min(S, j + 3) + 1):
                if k - i > 1 and m - j > 1:
                    continue
                d = segs[m - 1][1] - segs[j][0]
                s_ = sum(syl[i:k]) / rate
                cost = (d - s_) ** 2 / max(d, 0.3)
                cost += sum(0.35 for q in range(i, k - 1) if re.search(r"[.!?][\"”']?$", phrases[q]))
                cost += sum(1.5 * (segs[q + 1][0] - segs[q][1]) for q in range(j, m - 1))
                sub = best(k, m)
                if sub[0] + cost < out[0]:
                    out = (sub[0] + cost, ((i, k, j, m),) + sub[1])
        return out

    import sys  # noqa: PLC0415
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 4 * (P + S) + 200))
    try:
        cost, plan = best(0, 0)
    finally:
        sys.setrecursionlimit(old)
    words, phr = [], []
    for i, k, j, m in plan:
        a, b = segs[j][0], segs[m - 1][1]
        text = " ".join(phrases[i:k])
        ws = text.split()
        sy = [max(1, lang.syllables_spoken(w)) for w in ws]
        T = sum(sy)
        t = a
        phr.append({"text": text, "start": round(a, 3), "end": round(b, 3)})
        for w, s_ in zip(ws, sy):
            d = (b - a) * s_ / T
            words.append({"w": w, "start": round(t, 3), "end": round(t + d, 3)})
            t += d
    return words, phr, cost


def speech_segments(silent_runs, dur, min_len=0.08):
    """Đoạn có tiếng = phần bù của các khoảng lặng."""
    segs, cur = [], 0.0
    for a, b in silent_runs:
        if a - cur > min_len:
            segs.append([cur, a])
        cur = b
    if dur - cur > min_len:
        segs.append([cur, dur])
    return segs


def assign_lines(words, lines):
    """Gán từ (theo thứ tự) cho từng câu theo số token hiển thị của câu → [[words câu 1], …]."""
    out, i = [], 0
    for ln in lines:
        n = len(ln["text"].split())
        out.append(words[i:i + n])
        i += n
    if i < len(words) and out:
        out[-1] += words[i:]
    return out


def match_whisper(ww, lines):
    """Whisper trả từ của nó (có thể khác chữ hiển thị) → map tuần tự vào token hiển thị của từng câu."""
    toks = [(k, t) for k, ln in enumerate(lines) for t in ln["text"].split()]
    if not ww:
        return None
    out = []
    n, m = len(toks), len(ww)
    for idx, (k, t) in enumerate(toks):  # nội suy tỉ lệ khi số từ lệch nhau (số đọc thành nhiều từ…)
        a = ww[min(m - 1, int(idx * m / n))]
        b = ww[min(m - 1, max(int((idx + 1) * m / n) - 1, int(idx * m / n)))]
        out.append({"w": t, "line": k, "start": a["start"], "end": b["end"]})
    return out
