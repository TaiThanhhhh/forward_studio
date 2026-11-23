"""Hiệu ứng khung hình: zoom/punch-in, rung (trauma + noise), transition (flash, whip, glitch, fade ≤4f)."""

import numpy as np
from PIL import Image

from .common import H, W, channel, ease_out


def _hblur(arr, px):
    px = int(min(px, 90))
    if px < 2:
        return arr
    acc = np.zeros(arr.shape, np.float32)
    steps = 7
    for i in range(steps):
        acc += np.roll(arr, int(px * (i / (steps - 1) - 0.5)), axis=1)
    return (acc / steps).astype(np.uint8)


def transition(img, prev, kind, i):
    """Áp transition vào frame thứ i của shot mới (prev = frame sạch cuối của shot trước)."""
    tc = channel()["transitions"]
    if prev is None or kind in ("cut", "match"):
        return img
    if kind == "flash":
        nf, dec = tc["flash_frames"], tc["flash_decay_frames"]
        if i < nf:
            return Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.92)
        if i < nf + dec:
            return Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * (1 - (i - nf + 1) / (dec + 1)))
        return img
    if kind == "whip":
        n = tc["whip_frames"]
        if i >= n:
            return img
        p = ease_out((i + 1) / (n + 1))
        a_prev, a_new = np.asarray(prev), np.asarray(img)
        off = int(p * W)
        comp = np.empty_like(a_new)
        comp[:, : W - off] = a_prev[:, off:]
        comp[:, W - off:] = a_new[:, :off]
        return Image.fromarray(_hblur(comp, 110 * (1 - abs(2 * p - 1)) + 12))
    if kind == "glitch":
        if i >= tc["glitch_frames"]:
            return img
        a = np.asarray(img).copy()
        sh = 18 - i * 5
        a[..., 0] = np.roll(a[..., 0], sh, axis=1)
        a[..., 2] = np.roll(a[..., 2], -sh, axis=1)
        rng = np.random.default_rng(i)
        for _ in range(5):
            y = int(rng.integers(0, H - 80))
            h = int(rng.integers(10, 80))
            a[y:y + h] = np.roll(a[y:y + h], int(rng.integers(-50, 50)), axis=1)
        return Image.fromarray(a)
    if kind == "fade":
        n = min(4, tc["max_crossfade_frames"])
        return Image.blend(prev, img, (i + 1) / (n + 1)) if i < n else img
    if kind == "dip":
        # chuyển êm qua một nhịp tối nhẹ (4 frame) — làm mượt khi đổi giữa 2D html nền đen ↔ 3D three.js
        n = min(4, tc["max_crossfade_frames"])
        if i >= n:
            return img
        p = ease_out((i + 1) / (n + 1))
        blended = Image.blend(prev, img, p)
        dark = Image.new("RGB", (W, H), (8, 9, 12))
        dip = 0.42 * (1.0 - abs(2.0 * p - 1.0))
        return Image.blend(blended, dark, dip)
    return img
