"""Camera MỘT máy chạy liên tục trên mặt bảng (world → màn hình).

keys = [{"t", "cx", "cy", "zoom", "rot", "ease"}] — `ease` của key B là easing đi từ A tới B (lib/motion: smooth,
easeOut, easeIn, back, linear…). Zoom nội suy trong không gian log (đẩy/kéo đều mắt), rot tính bằng độ.
Cặp key chuẩn của ngữ pháp evidence board: một key "di chuyển ngắn" (easeOut/smooth) rồi một key "trôi chậm" (linear).
"""
import math

import numpy as np

import lib.motion as M


def at(keys, t):
    """(cx, cy, zoom, rot) tại thời điểm t (giây)."""
    if not keys:
        return (0.0, 0.0, 1.0, 0.0)
    if t <= keys[0]["t"]:
        k = keys[0]
        return (k["cx"], k["cy"], k["zoom"], k.get("rot", 0.0))
    for a, b in zip(keys, keys[1:]):
        if a["t"] <= t <= b["t"]:
            span = max(b["t"] - a["t"], 1e-9)
            u = M.EASE.get(b.get("ease") or "smooth", M.smooth)((t - a["t"]) / span)
            z = math.exp(math.log(a["zoom"]) + (math.log(b["zoom"]) - math.log(a["zoom"])) * u)
            return (a["cx"] + (b["cx"] - a["cx"]) * u, a["cy"] + (b["cy"] - a["cy"]) * u, z,
                    a.get("rot", 0.0) + (b.get("rot", 0.0) - a.get("rot", 0.0)) * u)
    k = keys[-1]
    return (k["cx"], k["cy"], k["zoom"], k.get("rot", 0.0))


def world_M(C, W, H):
    """Ma trận affine 2×3 world → màn hình."""
    cx, cy, z, r = C
    a = math.radians(-r)
    c, s = math.cos(a) * z, math.sin(a) * z
    return np.array([[c, -s, W / 2 - c * cx + s * cy], [s, c, H / 2 - s * cx - c * cy]], np.float64)


def to_screen(p, C, W, H):
    cx, cy, z, r = C
    a = math.radians(-r)
    x, y = (p[0] - cx) * z, (p[1] - cy) * z
    return (x * math.cos(a) - y * math.sin(a) + W / 2, x * math.sin(a) + y * math.cos(a) + H / 2)


def to_world(q, C, W, H):
    cx, cy, z, r = C
    a = math.radians(r)
    x, y = (q[0] - W / 2) / z, (q[1] - H / 2) / z
    return (x * math.cos(a) - y * math.sin(a) + cx, x * math.sin(a) + y * math.cos(a) + cy)


def motion_px(C0, C1, W, H):
    """Độ dịch chuyển lớn nhất (px) của 4 góc + tâm màn hình giữa hai trạng thái camera — đo 'đứng hình'."""
    pts = [(0, 0), (W, 0), (0, H), (W, H), (W / 2, H / 2)]
    best = 0.0
    for q in pts:
        w = to_world(q, C0, W, H)
        q2 = to_screen(w, C1, W, H)
        best = max(best, math.hypot(q2[0] - q[0], q2[1] - q[1]))
    return best
