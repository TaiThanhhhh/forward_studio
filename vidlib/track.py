"""Bám vật thể trên clip đã trim (nền đen → tách tiền cảnh rất dễ).

Selector một vật (khai báo ở storyboard `objects`):
  {"color": "red|blue|white|grey|bright", "near": [x, y], "largest": true}   — theo màu (bảng màu brand cố định:
      bi nóng = đỏ, đá/kính = xanh, nhân vật/đồ vật = trắng/xám)
  {"bbox": [x, y, w, h]}                                                       — theo vùng (KLT optical flow)
Toạ độ chuẩn hoá 0–1 theo khung 1080×1920. Tất cả tính trên ảnh thu nhỏ (QA_W×QA_H) cho nhanh.
"""
import cv2
import numpy as np

from .common import H, W

SW, SH = 270, 480  # kích thước phân tích
SX, SY = W / SW, H / SH


def small(img):
    """PIL RGB full → np uint8 (SH, SW, 3)."""
    return np.asarray(img.resize((SW, SH)))


def color_mask(rgb, name):
    a = rgb.astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    if name == "red":
        m = (r > 140) & (r > g * 1.5) & (r > b * 1.5)
    elif name == "blue":
        m = (b > 130) & (b > r * 1.7) & (b > g * 1.25)
    elif name == "white":
        m = (mn > 185) & (mx - mn < 45)
    elif name == "grey":
        m = (mx > 95) & (mx < 225) & (mx - mn < 30)
    else:  # bright: mọi thứ không phải nền đen
        m = mx > 70
    return m.astype(np.uint8)


def fg_soft(rgb_full):
    """Mặt nạ tiền cảnh mềm (luma key) ở độ phân giải đầy đủ: 0 = nền đen, 1 = vật."""
    a = np.asarray(rgb_full, np.float32)
    luma = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    m = np.clip((luma - 22.0) / 38.0, 0, 1)
    return cv2.GaussianBlur(m, (0, 0), 1.6)


class ObjectTracker:
    def __init__(self, oid, sel):
        self.id = oid
        self.sel = sel or {}
        self.box = None       # (x, y, w, h) toạ độ phân tích
        self.mask = None      # mặt nạ vật (SH, SW)
        self.center = None    # (x, y) toạ độ phân tích, đã làm mượt
        self.history = []     # tâm theo từng frame (toạ độ đầy đủ)
        self._pts = None
        self._gray = None

    # -- kết quả theo toạ độ khung đầy đủ
    def box_full(self):
        if self.box is None:
            return None
        x, y, w, h = self.box
        return x * SX, y * SY, w * SX, h * SY

    def center_full(self):
        if self.center is None:
            return None
        return self.center[0] * SX, self.center[1] * SY

    def update(self, rgb_small, gray_small=None):
        if "bbox" in self.sel:
            self._update_klt(gray_small if gray_small is not None else cv2.cvtColor(rgb_small, cv2.COLOR_RGB2GRAY))
        else:
            self._update_color(rgb_small)
        if self.center is not None:
            self.history.append(self.center_full())
        return self

    def _update_color(self, rgb):
        m = color_mask(rgb, self.sel.get("color", "bright"))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        n, lab, stats, cents = cv2.connectedComponentsWithStats(m, 8)
        if n <= 1:
            return
        cand = [k for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] >= 12]
        if not cand:
            return
        if self.center is None:
            if self.sel.get("near"):
                nx, ny = self.sel["near"][0] * SW, self.sel["near"][1] * SH
                k = min(cand, key=lambda c: (cents[c][0] - nx) ** 2 + (cents[c][1] - ny) ** 2
                        - 0.15 * stats[c, cv2.CC_STAT_AREA])
            else:
                k = max(cand, key=lambda c: stats[c, cv2.CC_STAT_AREA])
        else:
            px, py = self.center
            prev_area = (self.box[2] * self.box[3]) if self.box else 1
            k = min(cand, key=lambda c: (cents[c][0] - px) ** 2 + (cents[c][1] - py) ** 2
                    + (0 if stats[c, cv2.CC_STAT_AREA] > 0.25 * prev_area else 400))
        x, y, w, h = (int(stats[k, i]) for i in (0, 1, 2, 3))
        cx, cy = cents[k]
        if self.center is not None:  # chống rung: nội suy về phía vị trí mới
            cx = 0.55 * cx + 0.45 * self.center[0]
            cy = 0.55 * cy + 0.45 * self.center[1]
        self.center = (float(cx), float(cy))
        self.box = (x, y, w, h)
        self.mask = (lab == k).astype(np.uint8)

    def _update_klt(self, gray):
        if self._gray is None:
            x, y, w, h = self.sel["bbox"]
            x, y, w, h = x * SW, y * SH, w * SW, h * SH
            self.box = (x, y, w, h)
            self.center = (x + w / 2, y + h / 2)
            roi = np.zeros_like(gray)
            roi[int(y):int(y + h), int(x):int(x + w)] = 255
            self._pts = cv2.goodFeaturesToTrack(gray, 60, 0.01, 3, mask=roi)
            self._gray = gray
            self.mask = (roi > 0).astype(np.uint8)
            return
        if self._pts is None or len(self._pts) < 4:
            self._gray = gray
            return
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(self._gray, gray, self._pts, None, winSize=(15, 15), maxLevel=2)
        good = st.reshape(-1) == 1
        if good.sum() >= 3:
            d = np.median((nxt[good] - self._pts[good]).reshape(-1, 2), axis=0)
            x, y, w, h = self.box
            self.box = (x + d[0], y + d[1], w, h)
            self.center = (self.center[0] + d[0], self.center[1] + d[1])
            self._pts = nxt[good].reshape(-1, 1, 2)
            self.mask = np.zeros_like(gray)
            bx, by, bw, bh = (int(v) for v in self.box)
            self.mask[max(0, by):by + bh, max(0, bx):bx + bw] = 1
        self._gray = gray

    def extreme_toward(self, target_full):
        """Điểm của vật xa nhất theo hướng tới target (dùng cho 'character_hand')."""
        if self.mask is None or self.center is None:
            return self.center_full()
        ys, xs = np.nonzero(self.mask)
        if not len(xs):
            return self.center_full()
        tx, ty = target_full[0] / SX, target_full[1] / SY
        cx, cy = self.center
        v = np.array([tx - cx, ty - cy], np.float32)
        v /= np.linalg.norm(v) + 1e-6
        proj = (xs - cx) * v[0] + (ys - cy) * v[1]
        i = int(np.argmax(proj))
        return xs[i] * SX, ys[i] * SY


