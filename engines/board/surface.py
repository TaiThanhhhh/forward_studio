"""Mặt bảng (world) + hậu kỳ toàn khung (grain, vignette, flicker, xử lý phim câm).

Bề mặt theo style (styles/<style>.json → "board"):
  board     giấy đen nhám, lưới mờ               (board-black)
  chalk     gần đen nhìn từ trên xuống, vệt phấn  (chalk-case-black)
  notebook  giấy ô li tông tối                    (lab-notebook-black)
  film      gần đen #0b0b0b, phim câm bạc         (silent-film-black)
Lưới vẽ theo toạ độ màn hình mỗi frame (luôn sắc ở mọi mức zoom); nền nhiễu nướng sẵn ở 0.5 px/đơn vị.
"""
import math

import cv2
import numpy as np

from . import camera
from . import color as col

BG_DENSITY = 0.5


def build_bg(ww, wh, tokens, seed=1):
    """Ảnh nền world (BGR uint8) ở BG_DENSITY px/đơn vị."""
    w, h = max(8, int(ww * BG_DENSITY)), max(8, int(wh * BG_DENSITY))
    rng = np.random.default_rng(seed)
    base = col.bgr_f(tokens.get("bg", "#0e0e0e"))
    bg = np.empty((h, w, 3), np.float32)
    bg[:] = base
    amp = float(tokens.get("bg_noise", 9))
    n = cv2.resize(rng.random((max(2, h // 24), max(2, w // 24))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    fine = rng.normal(0, 1, (h, w)).astype(np.float32)
    bg += ((n - 0.5) * amp + fine * amp * 0.18)[..., None]
    if tokens.get("surface") == "chalk":  # vệt phấn lau dở: mảng sáng rộng, mờ
        sm = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 40)
        sm = (sm - sm.min()) / (sm.max() - sm.min() + 1e-6)
        bg += (np.clip(sm - 0.55, 0, 1) * 34)[..., None]
    return np.clip(bg, 0, 255).astype(np.uint8)


def draw_bg(frame, bg, C, tokens):
    H, W = frame.shape[:2]
    Mw = camera.world_M(C, W, H)
    S = np.array([[1 / BG_DENSITY, 0, 0], [0, 1 / BG_DENSITY, 0], [0, 0, 1]])
    M2 = (np.vstack([Mw, [0, 0, 1]]) @ S)[:2]
    cv2.warpAffine(bg, M2, (W, H), dst=frame, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def draw_grid(frame, C, tokens, ww, wh):
    g = tokens.get("grid")
    if not g:
        return
    H, W = frame.shape[:2]
    corners = [camera.to_world(q, C, W, H) for q in ((0, 0), (W, 0), (0, H), (W, H))]
    x0, x1 = min(p[0] for p in corners), max(p[0] for p in corners)
    y0, y1 = min(p[1] for p in corners), max(p[1] for p in corners)
    major = int(g.get("major_every", 0) or 0)
    for step, colr, px in ((g["step"], g["color"], g.get("px", 1.5)),):
        bgr = col.bgr(colr)
        bgr_major = col.bgr(g.get("major_color", colr))
        wpx = max(1, int(round(px * C[2])))
        k0 = math.floor(x0 / step)
        for k in range(k0, int(x1 / step) + 2):
            x = k * step
            a, b = camera.to_screen((x, y0), C, W, H), camera.to_screen((x, y1), C, W, H)
            c = bgr_major if major and k % major == 0 else bgr
            cv2.line(frame, (int(a[0] * 16), int(a[1] * 16)), (int(b[0] * 16), int(b[1] * 16)), c, wpx, cv2.LINE_AA, 4)
        k0 = math.floor(y0 / step)
        for k in range(k0, int(y1 / step) + 2):
            y = k * step
            a, b = camera.to_screen((x0, y), C, W, H), camera.to_screen((x1, y), C, W, H)
            c = bgr_major if major and k % major == 0 else bgr
            cv2.line(frame, (int(a[0] * 16), int(a[1] * 16)), (int(b[0] * 16), int(b[1] * 16)), c, wpx, cv2.LINE_AA, 4)


class Post:
    """Grain + vignette + flicker (+ phim câm: đơn sắc bạc giữ đỏ, vết xước, bụi, rung khung)."""

    def __init__(self, W, H, tokens, seed=5):
        self.W, self.H, self.t = W, H, tokens
        yy, xx = np.ogrid[:H, :W]
        v = float(tokens.get("vignette", 0.42))
        r = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2
        self.vig = (1 - v * np.clip(r, 0, 1))[..., None].astype(np.float32)
        rng = np.random.default_rng(seed)
        sg = float(tokens.get("grain", 6.5))
        self.grains = [rng.normal(0, sg, (H, W, 1)).astype(np.float32) for _ in range(6)] if sg > 0 else None
        self.film = bool(tokens.get("film"))
        self.tint = col.bgr_f(tokens.get("film_tint", "#d8d8d2")) / 255.0

    def apply(self, frame, fi):
        r = np.random.default_rng(1000 + fi)
        fl = float(self.t.get("flicker", 0.02))
        k = 1.0 + (r.random() * 2 - 1) * fl
        f = frame.astype(np.float32)
        if self.film:
            f = film_grade(f, self.tint)
        f *= self.vig * k
        if self.grains:
            f += self.grains[fi % len(self.grains)]
        out = np.clip(f, 0, 255).astype(np.uint8)
        if self.film:
            out = scratches(out, r, int(self.t.get("scratches", 2)))
            out = gate_weave(out, r, float(self.t.get("weave", 1.6)))
        return out


def film_grade(f, tint):
    """Đơn sắc bạc, GIỮ đỏ accent (đỏ = ý nghĩa). f: float32 BGR."""
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    red = (r > g * 1.6) & (r > b * 1.6) & (r > 100)
    y = (0.114 * b + 0.587 * g + 0.299 * r)[..., None]
    mono = y * tint[None, None, :]
    return np.where(red[..., None], f * 0.85 + mono * 0.15, mono)


def scratches(out, r, nmax):
    H, W = out.shape[:2]
    for _ in range(int(r.integers(0, nmax + 1))):
        x = int(r.integers(0, W))
        c = (215, 215, 210) if r.random() < 0.6 else (30, 30, 30)
        cv2.line(out, (x, 0), (x + int(r.integers(-20, 20)), H), c, 1)
    for _ in range(int(r.integers(2, 8))):
        cv2.circle(out, (int(r.integers(0, W)), int(r.integers(0, H))), int(r.integers(1, 4)), (18, 18, 18), -1)
    return out


def gate_weave(out, r, amp):
    if amp <= 0:
        return out
    H, W = out.shape[:2]
    M = np.float32([[1, 0, r.normal(0, amp * 0.75)], [0, 1, r.normal(0, amp)]])
    return cv2.warpAffine(out, M, (W, H), borderMode=cv2.BORDER_REFLECT)
