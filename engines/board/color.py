"""Màu cho engine board — MỌI nơi ngoài file này chỉ nhập hex (#d0312d) hoặc bộ RGB.

OpenCV giữ frame theo thứ tự BGR; PIL vẽ theo RGB(A). Đảo nhầm là đỏ ↔ xanh (lỗi kinh điển của engine gốc
kaz-documentary: "Frames are BGR. Specify background colours in BGR"). Ở đây:
  - `rgb(c)`  → (r, g, b)  dùng cho PIL (sprite RGBA)
  - `bgr(c)`  → (b, g, r)  dùng cho cv2 vẽ thẳng lên frame
  - `sprite(img)` PIL RGBA → mảng BGRA premultiplied (để warp + blend không viền tối)
  - `to_rgb(frame)` frame BGR → RGB (PIL/contact sheet/QA)
tests/test_board.py vẽ một vạch accent rồi đọc lại pixel để chắc chắn đỏ vẫn là đỏ.
"""
import numpy as np


def rgb(c):
    """'#d0312d' | 'd0312d' | (r, g, b) | [r, g, b, a] → (r, g, b) int."""
    if isinstance(c, (tuple, list)):
        return tuple(int(v) for v in c[:3])
    s = str(c).strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"màu không hợp lệ: {c!r} (cần #rrggbb)")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rgba(c, a=255):
    return (*rgb(c), int(max(0, min(255, a))))


def bgr(c):
    r, g, b = rgb(c)
    return (b, g, r)


def bgr_f(c):
    """Mảng float32 (3,) theo BGR — để cộng/nhân trên frame float."""
    return np.array(bgr(c), np.float32)


def mix(c1, c2, t):
    a, b = rgb(c1), rgb(c2)
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def hexs(c):
    r, g, b = rgb(c)
    return f"#{r:02x}{g:02x}{b:02x}"


def sprite(img):
    """PIL RGBA → np.uint8 (h, w, 4) BGRA với màu đã nhân alpha (premultiplied)."""
    a = np.asarray(img.convert("RGBA"), dtype=np.uint16)
    out = np.empty(a.shape, np.uint8)
    al = a[..., 3]
    out[..., 0] = (a[..., 2] * al + 127) // 255
    out[..., 1] = (a[..., 1] * al + 127) // 255
    out[..., 2] = (a[..., 0] * al + 127) // 255
    out[..., 3] = al
    return out


def to_rgb(frame_bgr):
    return np.ascontiguousarray(frame_bgr[..., ::-1])


def from_rgb(arr_rgb):
    return np.ascontiguousarray(np.asarray(arr_rgb)[..., ::-1])
