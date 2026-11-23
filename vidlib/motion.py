"""Phân tích chuyển động → auto-trim chống khựng.

motion energy[i] = trung bình |frame[i] − frame[i−1]| (ảnh xám thu nhỏ, thang 0–255).
  - đầu tĩnh  : các frame đầu có energy < ngưỡng hoạt động (head_ratio giữa nền nhiễu và đỉnh).
  - đuôi giảm tốc: từ cuối clip đi ngược, các frame có energy < tail_ratio × mức hoạt động trung vị
                   (xác định bằng ngưỡng, không cắt cứng %).
  - scene cut : gai energy vượt scene_cut_ratio × trung vị và ≥ scene_cut_min → không cho cửa sổ cắt đi qua.
Cửa sổ dùng = đoạn liên tục dài đúng target × speed (giây nguồn) có tổng năng lượng cao nhất trong vùng sạch.
"""
import os
import subprocess

import numpy as np

from .common import FPS, StudioError, channel, ffbin, load_json, save_json


def read_gray(path, size=None, fps=None):
    """Đọc toàn bộ clip thành mảng (N, h, w) float32 xám, kích thước nhỏ cho nhanh."""
    w, h = size or channel()["trim"]["analysis_size"]
    fps = fps or FPS
    cmd = [ffbin("ffmpeg"), "-v", "error", "-i", path, "-an", "-vf", f"fps={fps},scale={w}:{h}:flags=area,format=gray",
           "-f", "rawvideo", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise StudioError(f"Không đọc được {path}: {r.stderr.decode('utf-8', 'replace')[-400:]}")
    n = len(r.stdout) // (w * h)
    return np.frombuffer(r.stdout[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)


def energy(frames, thr=None):
    """Năng lượng chuyển động: chỉ cộng các điểm ảnh đổi > thr mức xám (loại nhiễu nén/grain)."""
    if len(frames) < 2:
        return np.zeros(len(frames), np.float32)
    thr = channel()["trim"].get("diff_threshold", 10) if thr is None else thr
    d = np.abs(np.diff(frames, axis=0))
    d = np.where(d > thr, d, 0).mean(axis=(1, 2))
    return np.concatenate([[d[0]], d]).astype(np.float32)


def smooth(x, k):
    if k <= 1 or len(x) < k:
        return x.copy()
    pad = k // 2
    xp = np.pad(x, pad, mode="edge")
    return np.convolve(xp, np.ones(k) / k, mode="valid")[: len(x)]


def scene_cuts(e, ratio=None, floor=None):
    """Chỉ số frame bắt đầu cảnh mới (gai năng lượng đơn lẻ)."""
    t = channel()["trim"]
    ratio = ratio or t["scene_cut_ratio"]
    floor = floor or t["scene_cut_min"]
    if len(e) < 3:
        return []
    med = float(np.median(e[1:])) + 1e-3
    cuts = []
    for i in range(1, len(e)):
        nb = np.concatenate([e[max(1, i - 3):i], e[i + 1:i + 4]])
        local = float(np.median(nb)) if len(nb) else med
        if e[i] >= floor and e[i] >= ratio * max(local, med * 0.5):
            cuts.append(i)
    return cuts


def analyze(path=None, frames=None, fps=None):
    """Trả về dict phân tích (dùng được với clip giả trong test qua `frames`)."""
    t = channel()["trim"]
    fps = fps or FPS
    if frames is None:
        frames = read_gray(path, fps=fps)
    n = len(frames)
    e_raw = energy(frames)
    cuts = scene_cuts(e_raw)
    e = e_raw.copy()
    for c in cuts:  # gai scene cut không được tính là "hoạt động"
        e[c] = np.median(e_raw)
    es = smooth(e, t["smooth_frames"])
    noise = float(np.percentile(es[1:], 10)) if n > 2 else 0.0
    peak = float(np.percentile(es[1:], 90)) if n > 2 else 0.0
    thr_head = noise + t["head_ratio"] * (peak - noise)
    active = (peak - noise) > t.get("min_activity", 0.02) and peak > 2.5 * noise  # False = clip gần như tĩnh
    head = 0
    if active:
        above = np.nonzero(es >= thr_head)[0]
        head = int(above[0]) if len(above) else 0
    head = min(head, int(n * t["max_head_frac"]))
    tail = n
    if active and n - head > 4:
        level = float(np.median(es[head:])) if n - head > 0 else 0.0
        thr_tail = noise + t["tail_ratio"] * (level - noise)
        above = np.nonzero(es[head:] >= thr_tail)[0]
        if len(above):
            tail = head + int(above[-1]) + 1
        tail = max(tail, int(n * (1 - t["max_tail_frac"])))
    return {"frames": n, "fps": fps, "energy": [round(float(x), 3) for x in es], "noise": round(noise, 3),
            "peak": round(peak, 3), "head_end": head, "tail_start": tail, "cuts": cuts, "active": bool(active)}


def segments(a):
    """Các đoạn sạch [s, e) trong vùng [head_end, tail_start) không chứa scene cut."""
    bounds = [a["head_end"]] + [c for c in a["cuts"] if a["head_end"] < c < a["tail_start"]] + [a["tail_start"]]
    return [(s, e) for s, e in zip(bounds, bounds[1:]) if e - s > 0]


def choose_window(a, need, anchor="best"):
    """Chọn [in, out) dài `need` frame. anchor='end' → bám cuối vùng sạch (dùng cho clip làm nguồn seed)."""
    es = np.asarray(a["energy"], np.float32)
    segs = segments(a) or [(0, a["frames"])]
    seg = max(segs, key=lambda se: se[1] - se[0])
    s, e = seg
    if e - s <= need:
        # vùng sạch ngắn hơn nhu cầu: lấy trọn vùng, nới về phía đầu clip trước (đuôi giảm tốc là thứ gây khựng)
        lo = max(0, e - need)
        if lo < s and any(lo < c <= s for c in a["cuts"]):  # không được vắt qua scene cut
            lo = s
        return lo, min(a["frames"], lo + need), "short"
    if anchor == "end":
        return e - need, e, "end"
    if anchor == "start":  # shot nối tiếp: bắt đầu đúng lúc chuyển động bắt đầu (khung đầu = khung cuối shot trước)
        return s, s + need, "start"
    csum = np.concatenate([[0], np.cumsum(es[s:e])])
    best = int(np.argmax(csum[need:] - csum[:-need]))
    return s + best, s + best + need, "best"


def plan_trims(proj, sb, analyses, out_path=None):
    """Tạo work/trim.json: {sid: {in, out, speed, src_sec, ...}} (giây NGUỒN, trước speed)."""
    fps = FPS
    seed_sources = {s["start_frame"].get("seed_from") for s in sb["shots"] if s["start_frame"].get("seed_from")}
    plan = {}
    for s in sb["shots"]:
        sid = s["id"]
        a = analyses.get(sid)
        if not a:
            continue
        speed = float(s["trim"].get("speed") or 1.0)
        need = max(2, int(round(s["target_sec"] * speed * fps)))
        man_in, man_out = s["trim"].get("in"), s["trim"].get("out")
        if man_in is not None:
            fin = int(round(float(man_in) * fps))
            fout = int(round(float(man_out) * fps)) if man_out is not None else fin + need
            how = "thủ công"
        else:
            anchor = "end" if sid in seed_sources else ("start" if s["start_frame"].get("seed_from") else "best")
            fin, fout, how = choose_window(a, need, anchor)
        fout = min(fout, a["frames"])
        plan[sid] = {"in": round(fin / fps, 4), "out": round(fout / fps, 4), "speed": speed, "how": how,
                     "head_end": round(a["head_end"] / fps, 3), "tail_start": round(a["tail_start"] / fps, 3),
                     "cuts": [round(c / fps, 3) for c in a["cuts"]], "clip_sec": round(a["frames"] / fps, 3),
                     "short": how == "short"}
    if out_path:
        save_json(out_path, plan)
    return plan


def export_frame(video, t, out_png):
    """Xuất 1 frame tại giây t (PNG đủ phân giải) — dùng làm start frame cho shot nối tiếp."""
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    if os.path.exists(out_png):
        os.remove(out_png)
    # lùi nửa frame để -ss không rơi ra ngoài frame cuối; dự phòng: lấy frame cuối bằng -sseof
    for seek in (["-ss", f"{max(t - 0.5 / FPS, 0):.4f}"], ["-sseof", "-0.1"]):
        r = subprocess.run([ffbin("ffmpeg"), "-y", "-v", "error", *seek, "-i", video, "-frames:v", "1", out_png],
                           capture_output=True)
        if r.returncode == 0 and os.path.exists(out_png):
            break
    if not os.path.exists(out_png):
        raise StudioError(f"Không trích được frame {t:.2f}s từ {video}")
    return out_png


def seed_frames(proj, sb, trims, ingested_path):
    """Với shot có seed_from: xuất frame NGAY TRƯỚC vùng giảm tốc của clip nguồn (= điểm out của cửa sổ)."""
    made = []
    for s in sb["shots"]:
        src = s["start_frame"].get("seed_from")
        if not src or src not in trims:
            continue
        dst = os.path.join(proj, s["start_frame"]["file"])
        video = ingested_path(src)
        t_out = trims[src]["out"] - 1.0 / FPS
        stamp = os.path.join(proj, "work", "seeds.json")
        seeds = load_json(stamp, {})
        key = f"{src}@{t_out:.4f}:{os.path.getmtime(video):.0f}"
        if os.path.exists(dst) and seeds.get(s["id"]) == key:
            continue
        export_frame(video, t_out, dst)
        seeds[s["id"]] = key
        save_json(stamp, seeds)
        made.append((s["id"], src, t_out))
    return made


# ------------------------------------------------------------------ QA: vận tốc quanh điểm cắt
def centroid_velocity(frames):
    """Vector vận tốc (px/frame, thang ảnh phân tích) của trọng tâm vùng sáng giữa các frame liên tiếp."""
    vs = []
    prev = None
    for f in frames:
        m = f > 100
        if m.sum() < 4:
            c = None
        else:
            ys, xs = np.nonzero(m)
            c = np.array([xs.mean(), ys.mean()])
        if prev is not None and c is not None:
            vs.append(c - prev)
        prev = c
    return np.mean(vs, axis=0) if vs else np.zeros(2)


def velocity_mismatch(before, after):
    """0 = liền mạch, 1 = ngược hướng/chênh tốc tối đa. before/after: vài frame xám quanh điểm cắt."""
    va, vb = centroid_velocity(before), centroid_velocity(after)
    ea = float(np.abs(np.diff(before, axis=0)).mean()) if len(before) > 1 else 0.0
    eb = float(np.abs(np.diff(after, axis=0)).mean()) if len(after) > 1 else 0.0
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    vel = float(np.linalg.norm(va - vb) / (na + nb + 1e-6)) if na + nb > 0.3 else 0.0
    eng = abs(ea - eb) / (max(ea, eb) + 1e-6) if max(ea, eb) > 0.3 else 0.0
    return round(0.6 * vel + 0.4 * eng, 3), {"v_before": [round(float(x), 2) for x in va],
                                             "v_after": [round(float(x), 2) for x in vb],
                                             "energy_before": round(ea, 2), "energy_after": round(eb, 2)}
