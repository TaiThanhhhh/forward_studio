"""Vẽ lên frame BGR: dán sprite (warp vùng ROI, alpha premultiplied), ảnh/clip vào khung, nét vẽ tay đỏ.

Chỉ warp phần màn hình mà sprite phủ (ROI) thay vì cả frame như engine gốc → nhanh hơn nhiều khi có nhiều thẻ.
"""
import math

import cv2
import numpy as np

from . import camera
from . import color as col


class Sprite:
    """Ảnh BGRA premultiplied + mật độ D (px / đơn vị world) + điểm neo (px) ứng với tâm vật."""

    def __init__(self, arr, D, anchor=None):
        self.arr = arr
        self.D = float(D)
        h, w = arr.shape[:2]
        self.anchor = anchor if anchor is not None else (w / 2.0, h / 2.0)
        self._half = None

    @property
    def size_world(self):
        h, w = self.arr.shape[:2]
        return (w / self.D, h / self.D)

    def half(self):
        if self._half is None:
            h, w = self.arr.shape[:2]
            self._half = Sprite(cv2.resize(self.arr, (max(1, w // 2), max(1, h // 2)), interpolation=cv2.INTER_AREA),
                                self.D / 2, (self.anchor[0] / 2, self.anchor[1] / 2))
        return self._half


def item_M(center, rot, scale, C, W, H):
    """Affine 3×3: toạ độ cục bộ của vật (đơn vị world, gốc ở tâm, chưa xoay) → màn hình."""
    rr = math.radians(rot)
    c, s = math.cos(rr) * scale, math.sin(rr) * scale
    L = np.array([[c, -s, center[0]], [s, c, center[1]], [0, 0, 1]], np.float64)
    Wm = np.vstack([camera.world_M(C, W, H), [0, 0, 1]])
    return Wm @ L


def local_to_screen(p, center, rot, scale, C, W, H):
    m = item_M(center, rot, scale, C, W, H)
    v = m @ np.array([p[0], p[1], 1.0])
    return (float(v[0]), float(v[1]))


def _roi(M2, w, h, W, H, pad=2):
    pts = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float64).T
    q = M2 @ pts
    x0, y0 = max(0, int(math.floor(q[0].min())) - pad), max(0, int(math.floor(q[1].min())) - pad)
    x1, y1 = min(W, int(math.ceil(q[0].max())) + pad), min(H, int(math.ceil(q[1].max())) + pad)
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def blit(frame, spr, center, rot, C, scale=1.0, alpha=1.0, offset=(0.0, 0.0)):
    """Dán sprite tại `center` (world), xoay `rot` độ, phóng `scale`; `offset` = dời trong toạ độ cục bộ (world)."""
    if alpha <= 0.003:
        return
    H, W = frame.shape[:2]
    screen_scale = C[2] * scale / spr.D
    if screen_scale < 0.45 and spr.arr.shape[0] > 64:
        spr = spr.half()
        screen_scale *= 2
    m = item_M(center, rot, scale, C, W, H)
    S = np.array([[1 / spr.D, 0, offset[0] - spr.anchor[0] / spr.D], [0, 1 / spr.D, offset[1] - spr.anchor[1] / spr.D],
                  [0, 0, 1]])
    M2 = (m @ S)[:2]
    h, w = spr.arr.shape[:2]
    r = _roi(M2, w, h, W, H)
    if r is None:
        return
    x0, y0, x1, y1 = r
    M3 = M2.copy()
    M3[0, 2] -= x0
    M3[1, 2] -= y0
    warped = cv2.warpAffine(spr.arr, M3, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                            borderValue=(0, 0, 0, 0))
    over(frame, warped, x0, y0, alpha)


def over(frame, bgra_premul, x0, y0, alpha=1.0):
    """frame[y0:, x0:] = src + dst·(1 − a)  (src premultiplied)."""
    h, w = bgra_premul.shape[:2]
    dst = frame[y0:y0 + h, x0:x0 + w]
    src = bgra_premul[: dst.shape[0], : dst.shape[1]]
    a = src[..., 3:4].astype(np.float32) * (alpha / 255.0)
    if not a.any():
        return
    out = dst.astype(np.float32) * (1.0 - a) + src[..., :3].astype(np.float32) * alpha
    dst[:] = np.clip(out, 0, 255).astype(np.uint8)


def photo(frame, img, center, rot, scale, rect, C, edge_bgr=None):
    """Dán ảnh BGR `img` vào ô chữ nhật `rect` = (x0, y0, x1, y1) toạ độ cục bộ (world) của vật. Trả về True nếu
    ảnh phủ kín cả màn hình (camera đã 'chui' vào khung → chiếu toàn màn hình)."""
    H, W = frame.shape[:2]
    ih, iw = img.shape[:2]
    rw, rh = rect[2] - rect[0], rect[3] - rect[1]
    m = item_M(center, rot, scale, C, W, H)
    screen_scale = C[2] * scale * rw / iw
    src = img
    k = 1.0
    while screen_scale * k < 0.5 and src.shape[1] > 64:
        src = cv2.resize(src, (src.shape[1] // 2, src.shape[0] // 2), interpolation=cv2.INTER_AREA)
        k *= 2
    sh, sw = src.shape[:2]
    S = np.array([[rw / sw, 0, rect[0]], [0, rh / sh, rect[1]], [0, 0, 1]])
    M2 = (m @ S)[:2]
    corners = (M2 @ np.array([[0, 0, 1], [sw, 0, 1], [sw, sh, 1], [0, sh, 1]], np.float64).T).T
    covers = _covers(corners, W, H)
    r = _roi(M2, sw, sh, W, H, pad=1)
    if r is None:
        return False
    x0, y0, x1, y1 = r
    M3 = M2.copy()
    M3[0, 2] -= x0
    M3[1, 2] -= y0
    roi = frame[y0:y1, x0:x1]
    cv2.warpAffine(src, M3, (x1 - x0, y1 - y0), dst=roi, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
    if edge_bgr is not None and not covers:
        cv2.polylines(frame, [np.round(corners * 16).astype(np.int32)], True, edge_bgr, 2, cv2.LINE_AA, shift=4)
    return covers


def _covers(quad, W, H):
    """4 góc màn hình đều nằm trong tứ giác `quad` (lồi, theo thứ tự)."""
    q = quad.astype(np.float32).reshape(-1, 1, 2)
    return all(cv2.pointPolygonTest(q, (float(x), float(y)), False) >= 0 for x, y in ((0, 0), (W - 1, 0), (0, H - 1),
                                                                                       (W - 1, H - 1)))


def polyline(frame, pts, bgr, width, alpha=1.0, closed=False):
    """Nét chống răng cưa; alpha < 1 vẽ qua lớp phụ trong ROI."""
    if len(pts) < 2:
        return
    P = np.round(np.asarray(pts, np.float64) * 16).astype(np.int32)
    wpx = max(1, int(round(width)))
    if alpha >= 0.995:
        cv2.polylines(frame, [P], closed, bgr, wpx, cv2.LINE_AA, shift=4)
        return
    H, W = frame.shape[:2]
    xs, ys = P[:, 0] / 16, P[:, 1] / 16
    x0, y0 = max(0, int(xs.min()) - wpx - 2), max(0, int(ys.min()) - wpx - 2)
    x1, y1 = min(W, int(xs.max()) + wpx + 3), min(H, int(ys.max()) + wpx + 3)
    if x1 <= x0 or y1 <= y0:
        return
    roi = frame[y0:y1, x0:x1]
    layer = roi.copy()
    P2 = P - np.array([x0 * 16, y0 * 16], np.int32)
    cv2.polylines(layer, [P2], closed, bgr, wpx, cv2.LINE_AA, shift=4)
    cv2.addWeighted(layer, alpha, roi, 1 - alpha, 0, dst=roi)


def dot(frame, p, r, bgr, alpha=1.0):
    if alpha <= 0.01:
        return
    if alpha >= 0.995:
        cv2.circle(frame, (int(round(p[0] * 16)), int(round(p[1] * 16))), int(round(r * 16)), bgr, -1, cv2.LINE_AA, shift=4)
        return
    H, W = frame.shape[:2]
    x0, y0 = max(0, int(p[0] - r - 2)), max(0, int(p[1] - r - 2))
    x1, y1 = min(W, int(p[0] + r + 3)), min(H, int(p[1] + r + 3))
    if x1 <= x0 or y1 <= y0:
        return
    roi = frame[y0:y1, x0:x1]
    layer = roi.copy()
    cv2.circle(layer, (int(round((p[0] - x0) * 16)), int(round((p[1] - y0) * 16))), int(round(r * 16)), bgr, -1,
               cv2.LINE_AA, shift=4)
    cv2.addWeighted(layer, alpha, roi, 1 - alpha, 0, dst=roi)


def wobble_ellipse_pts(c, rx, ry, rot, frac, seed=0.0, n=96):
    """Vòng tròn vẽ tay (world): bắt đầu ở 'giờ 8', vòng 1.08 lần (đầu-cuối chồng nhau), bán kính rung nhẹ."""
    k = max(2, int(n * frac) + 2)
    rr = math.radians(rot)
    out = []
    for i in range(k):
        u = min(frac, i / (n - 1))
        th = -2.3 + 2 * math.pi * 1.08 * u
        jit = 1 + 0.045 * math.sin(i * 0.7 + seed) + 0.02 * math.sin(i * 0.23 + seed * 3)
        x, y = rx * jit * math.cos(th), ry * jit * math.sin(th) * (1 + 0.06 * u)
        out.append((c[0] + x * math.cos(rr) - y * math.sin(rr), c[1] + x * math.sin(rr) + y * math.cos(rr)))
    return out


def string_pts(a, b, u, sag, n=24):
    """Dây đỏ kéo từ a tới b (world), võng `sag` ở giữa; u ∈ [0, 1] = phần đã kéo."""
    out = []
    for i in range(n + 1):
        s = u * i / n
        x = a[0] + (b[0] - a[0]) * s
        y = a[1] + (b[1] - a[1]) * s + math.sin(s * math.pi) * sag * (0.4 + 0.6 * u)
        out.append((x, y))
    return out


def to_px(pts, C, W, H):
    return [camera.to_screen(p, C, W, H) for p in pts]


def rgb_split(f, px):
    """Tách kênh đỏ/xanh lam theo chiều ngang `px` pixel (đóng dấu, flash)."""
    if px == 0:
        return f
    out = f.copy()
    out[..., 2] = np.roll(f[..., 2], px, axis=1)
    out[..., 0] = np.roll(f[..., 0], -px, axis=1)
    return out


def bgr_of(c):
    return col.bgr(c)
