"""Dòng thời gian dựng: thời lượng shot (khớp VO), điểm cắt (snap beat), punch-in tự động, transition an toàn."""
import math

import numpy as np

from .common import FPS, channel


def shot_durations(sb, vo):
    """Thời lượng từng shot (giây). Có VO: mỗi câu phủ các shot của nó, co/giãn tỉ lệ cho khớp câu."""
    durs = [float(s["target_sec"]) for s in sb["shots"]]
    if not vo:
        return durs, []
    notes = []
    lines = vo["lines"]
    # điểm cắt đặt 0–3 frame TRƯỚC câu VO mới (phản ứng hình ảnh luôn đi trước lời)
    lead = min(3, max(0, channel()["vo"].get("react_lead_default", 2))) / FPS
    for k, ln in enumerate(lines):
        start = 0.0 if k == 0 else max(0.0, ln["start"] - lead)
        end = max(0.0, lines[k + 1]["start"] - lead) if k + 1 < len(lines) else ln["end"] + 0.35
        span = max(0.4, end - start)
        planned = sum(durs[i] for i in ln["shots"])
        for i in ln["shots"]:
            durs[i] = durs[i] * span / max(planned, 1e-6)
    # shot đứng TRƯỚC câu VO đầu tiên (không có lời) giữ nguyên
    mx = channel()["pacing"]["shot_max_sec"]
    for i, d in enumerate(durs):
        if d > mx + 0.6:
            notes.append(f"{sb['shots'][i]['id']}: dài {d:.1f}s sau khi khớp lời đọc (> {mx}s) — "
                         "tách câu VO hoặc thêm shot.")
    return durs, notes


def snap_to_beats(cuts, beats, max_frames):
    """Dời mỗi điểm cắt tới beat gần nhất nếu lệch ≤ max_frames."""
    if beats is None or not len(beats):
        return cuts
    tol = max_frames / FPS
    out = []
    for c in cuts:
        j = int(np.argmin(np.abs(beats - c)))
        out.append(float(beats[j]) if abs(beats[j] - c) <= tol else c)
    return out


def _onscreen_times(s, scale):
    return sorted(float(o.get("t", 0)) * scale for o in s.get("onscreen") or []
                  if o.get("kind") != "caption")


def punch_plan(s, dur, scale, idx):
    """Danh sách (t, scale) — punch-in xen kẽ để mỗi ≤ change_every giây có một thay đổi thị giác."""
    p = channel()["pacing"]
    lo, hi = p["punch_in_scale"]
    every = p["change_every_sec"]
    events = [0.0] + _onscreen_times(s, scale)
    punches = [float(t) * scale for t in s.get("punch_in") or []]
    events += punches
    events = sorted(set(round(t, 3) for t in events if 0 <= t < dur))
    auto = []
    bounds = events + [dur]
    for a, b in zip(bounds, bounds[1:]):
        gap = b - a
        if gap > every:
            n = int(math.ceil(gap / every)) - 1
            for k in range(1, n + 1):
                auto.append(a + gap * k / (n + 1))
    allp = sorted(punches + auto)
    out, level = [], 1.0
    for k, t in enumerate(allp):
        level = (lo + (hi - lo) * ((k + idx) % 2)) if level == 1.0 else 1.0
        out.append((round(t, 3), round(level, 3)))
    return out, len(auto)


def guard_flashes(trans, starts):
    """Không quá max_flashes_per_sec flash trong mọi cửa sổ 1 giây (WCAG 2.3.1)."""
    mx = channel()["transitions"]["max_flashes_per_sec"]
    out, recent, dropped = [], [], []
    for tr, t in zip(trans, starts):
        if tr == "flash":
            recent = [x for x in recent if t - x < 1.0]
            if len(recent) >= mx:
                out.append("cut")
                dropped.append(t)
                continue
            recent.append(t)
        out.append(tr)
    return out, dropped


def build(sb, vo=None, beats=None, outro_sec=0.0):
    durs, notes = shot_durations(sb, vo)
    starts, t = [], 0.0
    for d in durs:
        starts.append(t)
        t += d
    cuts = snap_to_beats(starts[1:] + [t], beats, channel()["audio"]["beat_snap_frames"]) if beats is not None \
        else starts[1:] + [t]
    bounds = [0.0] + cuts
    fb = [int(round(x * FPS)) for x in bounds]
    for i in range(1, len(fb)):  # mỗi shot tối thiểu 6 frame
        fb[i] = max(fb[i], fb[i - 1] + 6)
    trans = [("cut" if i == 0 else s.get("transition_in", "cut")) for i, s in enumerate(sb["shots"])]
    trans, dropped = guard_flashes(trans, [f / FPS for f in fb[:-1]])
    if dropped:
        notes.append(f"Bỏ {len(dropped)} flash để không vượt {channel()['transitions']['max_flashes_per_sec']} flash/giây.")
    segs, autos = [], 0
    for i, s in enumerate(sb["shots"]):
        n = fb[i + 1] - fb[i]
        dur = n / FPS
        scale = dur / max(float(s["target_sec"]), 1e-6)
        punches, na = punch_plan(s, dur, scale, i)
        autos += na
        base = 1.0 if i % 2 == 0 else 1.04
        continuing = i > 0 and (s.get("start_frame", {}).get("seed_from") or trans[i] == "match")
        if continuing:  # shot nối liền: giữ đúng mức zoom cuối của shot trước, không nhảy khung
            prev = segs[-1]
            base = min(1.2, prev["zoom_base"] * (prev["punches"][-1][1] if prev["punches"] else 1.0))
            punches = [(t, lv) for t, lv in punches if t > 0.4]
        segs.append({"sid": s["id"], "index": i, "start_f": fb[i], "n": n, "dur": round(dur, 4), "scale": round(scale, 4),
                     "transition": trans[i], "punches": punches, "zoom_base": round(base, 4),
                     "shake": s.get("beat") in ("payoff",) and trans[i] == "flash"})
    total_f = fb[-1]
    if outro_sec > 0:
        n = int(round(outro_sec * FPS))
        segs.append({"sid": "OUTRO", "index": len(segs), "start_f": total_f, "n": n, "dur": n / FPS, "scale": 1.0,
                     "transition": "whip", "punches": [], "zoom_base": 1.0, "shake": False})
        total_f += n
    return {"fps": FPS, "frames": total_f, "duration": round(total_f / FPS, 3), "segments": segs,
            "auto_punches": autos, "notes": notes, "beats_used": beats is not None}
