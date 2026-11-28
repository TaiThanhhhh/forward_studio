"""Chuyển cảnh `zoom_through` (vòng 21) — camera lao XUYÊN một bộ phận của shot trước (mắt, não, tim, cửa sổ, màn hình…)
và cảnh sau mở ra từ bên trong bộ phận đó.

Hai đường dựng:
- html → html trong cú máy liền (spine): kiểu bay `portal` — engine vẽ lại vector ở mọi độ phóng (core.js), file này
  chỉ quyết định đặt `portal` vào chuỗi kiểu bay (spine.py gọi `portal_tile`).
- mọi cặp khác (three.js, Flow, board, html không liền mạch): hậu kỳ trong render.py —
  đuôi shot trước: phóng tới ZMAX về điểm đích, điểm đích trôi dần về tâm khung (ease-in, có vệt mờ chuyển động);
  đầu shot sau: lộ qua LỖ TRÒN đúng cỡ bộ phận (đã phóng) rồi nở ra phủ khung, phần ngoài lỗ là khung cuối shot trước
  tiếp tục lao vào; cảnh sau tự lùi nhẹ 1.22× → 1× (quán tính tiến tới).

Điểm đích `through` (ghi trên shot SAU): "hero.eye" | "hero" (id actor của beat `scene` shot trước — toạ độ thật đọc từ
meta.json → anchors_end do engine html ghi khi job có `anchors_out`) | [x, y] | {x, y, r} (0..1 của khung shot trước).
Không có / không tìm thấy → tâm khung (shot three.js có `frame.dive` đã tự đưa bộ phận về tâm).
"""
import json
import math
import os

import numpy as np
from PIL import Image

from .common import H, W, color

OUT_FRAMES = 10            # đuôi shot trước
IN_FRAMES = 9              # đầu shot sau
ZMAX = 3.4                 # độ phóng cuối shot trước
_DIST = {}


def _dist(w, h):
    key = (w, h)
    if key not in _DIST:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _DIST[key] = np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2)
    return _DIST[key]


def _ease_in(p):
    p = min(1.0, max(0.0, p))
    return p * p * p


def _ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def _smooth(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def parse_through(through, w=W, h=H):
    """(x, y, r) px từ dạng toạ độ; None nếu là tên neo (chuỗi) hoặc rỗng."""
    if isinstance(through, (list, tuple)) and len(through) >= 2:
        r = float(through[2]) if len(through) > 2 else 0.05
        return float(through[0]) * w, float(through[1]) * h, max(4.0, r * h)
    if isinstance(through, dict) and "x" in through and "y" in through:
        return float(through["x"]) * w, float(through["y"]) * h, max(4.0, float(through.get("r", 0.05)) * h)
    return None


def through_errors(through, prev_shot=None):
    """Lỗi (tiếng Việt) của trường `through`; kiểm id/part theo beat `scene` của shot trước nếu có."""
    if through is None:
        return []
    if isinstance(through, (list, tuple)):
        ok = len(through) in (2, 3) and all(isinstance(v, (int, float)) for v in through) and \
            0 <= through[0] <= 1 and 0 <= through[1] <= 1
        return [] if ok else ["through [x, y(, r)] là toạ độ 0..1 của khung shot trước."]
    if isinstance(through, dict):
        ok = all(isinstance(through.get(k), (int, float)) for k in ("x", "y")) and \
            0 <= through["x"] <= 1 and 0 <= through["y"] <= 1
        return [] if ok else ["through {x, y, r} là toạ độ 0..1 của khung shot trước."]
    if not isinstance(through, str) or not through.strip():
        return ["through là \"id.part\" (vd \"hero.eye\"), [x, y] hoặc {x, y, r}."]
    code = (prev_shot or {}).get("code") or {}
    if code.get("scene") == "scene" and code.get("engine", "html") in ("html", None):
        from engines import html  # noqa: PLC0415
        e = html.ref_error(through, html.actor_ids(code.get("params") or {}), "through")
        return [e] if e else []
    if code.get("scene") == "stage":
        ids = [p.get("id") for p in (code.get("params") or {}).get("props") or [] if isinstance(p, dict)]
        aid = through.split(".")[0]
        if aid not in ids:
            have = ", ".join(i for i in ids if i) or "—"
            return [f"through: shot trước (three.js stage) không có prop '{aid}' (có: {have})."]
    return []


def anchors_end(proj, sid):
    """{tên neo: [X, Y, R]} ở frame cuối của shot code html (meta.json); {} nếu không có."""
    from . import codeshot  # noqa: PLC0415
    p = os.path.join(codeshot.code_dir(proj, sid), "meta.json")
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            return dict(json.load(fh).get("anchors_end") or {})
    except (OSError, ValueError):
        return {}


def target(proj, prev_shot, shot, w=W, h=H):
    """(x, y, r) px của điểm đích trên khung CUỐI shot trước."""
    th = (shot or {}).get("through")
    xy = parse_through(th, w, h)
    if xy:
        return xy
    if isinstance(th, str) and prev_shot:
        an = anchors_end(proj, prev_shot["id"])
        hit = an.get(th) or an.get(th.split(".")[0])
        if hit and len(hit) >= 2:
            r = float(hit[2]) if len(hit) > 2 else 0.05 * h
            return float(hit[0]), float(hit[1]), max(4.0, r)
    return w / 2, h / 2, 0.06 * h


def _zoom_about(img, tx, ty, scale, bg):
    """Phóng `scale` lần về điểm (tx, ty), điểm đó ra giữa khung (ngoài ảnh nguồn → màu nền)."""
    w, h = img.size
    inv = 1.0 / max(1e-6, scale)
    return img.transform((w, h), Image.AFFINE, (inv, 0.0, tx - w / 2 * inv, 0.0, inv, ty - h / 2 * inv),
                         resample=Image.BICUBIC, fillcolor=bg)


def _out_state(e, tgt, w, h):
    """(cx, cy, scale) của đuôi shot trước ở tiến độ e∈[0,1]: điểm nhìn trôi từ tâm khung tới đích, phóng 1 → ZMAX."""
    tx, ty, _ = tgt
    k = _smooth(min(1.0, e * 1.4))
    return w / 2 + (tx - w / 2) * k, h / 2 + (ty - h / 2) * k, math.exp(math.log(ZMAX) * _ease_in(e))


def apply_out(img, i, n, tgt):
    """Frame i của shot trước (n frame): phần đuôi lao về điểm đích."""
    win = min(OUT_FRAMES, max(2, n // 2))
    rem = n - i
    if rem > win:
        return img
    e = (win - rem + 1) / win
    cx, cy, sc = _out_state(e, tgt, *img.size)
    bg = tuple(color("bg"))
    out = _zoom_about(img, cx, cy, sc, bg)
    if e > 0.45:                                  # vệt mờ chuyển động hướng tâm: chồng một bản phóng nhỏ hơn
        ghost = _zoom_about(img, cx, cy, sc * 0.93, bg)
        out = Image.blend(out, ghost, 0.28 * (e - 0.45) / 0.55)
    return out


def apply_in(img, prev, i, tgt):
    """Frame i của shot sau: lộ qua lỗ tròn (cỡ bộ phận đã phóng) nở ra; ngoài lỗ = khung cuối shot trước lao tiếp."""
    if i >= IN_FRAMES:
        return img
    w, h = img.size
    e = (i + 1) / (IN_FRAMES + 1)
    bg = tuple(color("bg"))
    # cảnh sau tiến tới: 1.22× → 1×
    s_in = 1.0 + 0.22 * (1 - _ease_out(e))
    inner = _zoom_about(img, w / 2, h / 2, s_in, bg) if s_in > 1.001 else img
    if prev is None:
        return inner
    prev = prev if prev.size == img.size else prev.resize(img.size, Image.BICUBIC)
    tx, ty, tr = tgt
    sc_prev = ZMAX * (1 + 2.6 * _ease_in(e) + 0.6 * e)
    outer = _zoom_about(prev, tx, ty, sc_prev, bg)
    r0 = max(12.0, tr * ZMAX)
    rmax = math.hypot(w, h) / 2 + 24
    rad = r0 * math.exp(math.log(rmax / r0) * _ease_out(e) ** 1.15)
    feather = 10.0
    m = np.clip((rad - _dist(w, h)) / feather + 0.5, 0.0, 1.0)[..., None]
    a_in = np.asarray(inner, dtype=np.float32)
    a_out = np.asarray(outer, dtype=np.float32)
    # viền sáng mảnh quanh lỗ (mép bộ phận) cho mắt bám theo
    ring = np.clip(1 - np.abs(_dist(w, h) - rad) / 3.0, 0, 1)[..., None] * 0.35 * (1 - e)
    comp = a_in * m + a_out * (1 - m)
    comp = comp * (1 - ring) + 255.0 * ring
    return Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8))
