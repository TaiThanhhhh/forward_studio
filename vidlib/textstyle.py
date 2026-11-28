"""Kiểu chữ theo style (styles/*.json): render chữ thành sprite RGBA "vẽ cùng nét" với animation.

Mỗi lần render trả về `Art`: ảnh ghép hoàn chỉnh + từng chữ cái (để làm hiệu ứng theo từng chữ: viết dần, rơi,
vỡ văng…). Texture (phấn, bút lông), ống neon, bóng đổ, khung nổ truyện tranh được dựng ở đây; chuyển động và
tương tác với cảnh nằm ở textfx.py.
"""
import json
import math
import os
import zlib
from dataclasses import dataclass, field
from functools import lru_cache, cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .common import FONT_DIR, ROOT, StudioError, color, glyph_safe

STYLES_DIR = os.path.join(ROOT, "styles")
DEFAULTS = {"size": 120, "uppercase": True, "fill": "#FFFFFF", "stroke": 0, "stroke_color": "#000000",
            "outline_only": 0, "texture": None, "glow": None, "shadow": None, "letter_colors": None,
            "letter_jitter_deg": 0, "intro": "pop", "intro_frames": 8, "boil": {"px": 0.8, "every": 2},
            "underline": False, "leader_line": None, "paper_edge": None, "number_fill": None,
            "sfx_role": {"size_mult": 1.3, "rotate": -6}, "frost_color": "#9FC0FF", "heat_color": "#FF2D2D"}


# Vòng 21: style vòng 19 từng đặt theo tên kênh có thật → đổi sang tên thể loại (tên thương hiệu lọt vào brief rồi vào
# metadata khán giả thấy). Bí danh giữ cho storyboard/plan cũ chạy tiếp; không liệt kê bí danh trong list_styles().
STYLE_ALIASES = {
    "kurzgesagt-black": "cosmic-flat-black",
    "school-of-life-black": "essay-ink-black",
    "infographics-show-black": "bold-infographic-black",
}


def canonical(name):
    """Tên style chuẩn (bí danh cũ → id mới; tên khác giữ nguyên)."""
    return STYLE_ALIASES.get(name, name) if isinstance(name, str) else name


def list_styles():
    return sorted(os.path.splitext(f)[0] for f in os.listdir(STYLES_DIR) if f.endswith(".json"))


@cache
def load_style(name):
    name = canonical(name)
    p = os.path.join(STYLES_DIR, f"{name}.json")
    if not os.path.exists(p):
        raise StudioError(f"Không có style '{name}'. Có: {', '.join(list_styles())}")
    with open(p, encoding="utf-8") as f:
        st = {**DEFAULTS, **json.load(f)}
    st["id"] = name
    from . import lang  # noqa: PLC0415 — dự án tiếng Việt cũ: font có dấu
    if lang.language() == "vi" and st.get("font_vi"):
        st["font"] = st["font_vi"]
    return st


@lru_cache(maxsize=64)
def style_font(fname, size, variation=None):
    path = os.path.join(FONT_DIR, fname)
    if not os.path.exists(path):
        raise StudioError(f"Thiếu font {fname} trong assets/fonts/")
    f = ImageFont.truetype(path, int(size))
    if variation:
        try:
            f.set_variation_by_name(variation)
        except Exception:  # noqa: BLE001
            pass
    return f


@dataclass
class Art:
    img: Image.Image                        # RGBA ghép hoàn chỉnh (kể cả bóng, glow, khung nổ)
    letters: list = field(default_factory=list)  # [(RGBA, x, y)] toạ độ trong img (chưa có glow/bóng)
    box: tuple = (0, 0, 0, 0)               # bbox phần chữ trong img
    fill: tuple = (255, 255, 255)           # màu chữ chính (dùng cho OCR theo màu)
    style: str = "forward"
    role: str = "main"
    text: str = ""
    size: int = 100
    glow: dict = None


def seed(*parts):
    """Hạt giống ổn định giữa các lần chạy (hash() của Python bị ngẫu nhiên hoá)."""
    return zlib.crc32(repr(parts).encode("utf-8"))


def _rng(*key):
    return np.random.default_rng(seed(*key))


def _texture(alpha, kind, seed):
    """alpha: np.uint8 (h, w) → alpha đã "rỗ" theo chất liệu."""
    if not kind:
        return alpha
    h, w = alpha.shape
    rng = np.random.default_rng(seed)
    a = alpha.astype(np.float32) / 255.0
    if kind == "chalk":
        n = rng.random((h, w)).astype(np.float32)
        k = np.zeros((9, 9), np.float32)
        cv2.line(k, (0, 6), (8, 2), 1.0, 1)  # vệt phấn nghiêng
        streak = cv2.filter2D(n, -1, k / k.sum())
        grain = cv2.GaussianBlur(n, (0, 0), 0.7)
        m = np.clip((0.55 * streak + 0.45 * grain - 0.36) * 4.0, 0, 1)
        a = a * (0.18 + 0.82 * m)
    elif kind == "brush":
        rows = cv2.GaussianBlur(rng.random((h, 1)).astype(np.float32), (0, 0), 1.2)
        n = cv2.blur(rng.random((h, w)).astype(np.float32), (41, 1))
        m = np.clip((0.6 * n + 0.4 * rows - 0.33) * 5.0, 0, 1)
        a = a * (0.25 + 0.75 * m)
    return (np.clip(a, 0, 1) * 255).astype(np.uint8)


def _outline(alpha, width):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * width + 1, 2 * width + 1))
    dil = cv2.dilate(alpha, k)
    ero = cv2.erode(alpha, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return cv2.subtract(dil, ero)


def _burst(size, box, spec, seed):
    """Khung nổ răng cưa sau chữ tượng thanh."""
    w, h = size
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2 + spec.get("pad", 40), (y1 - y0) / 2 + spec.get("pad", 40)
    n = spec.get("spikes", 12)
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(2 * n):
        a = math.pi * i / n + rng.uniform(-0.08, 0.08)
        k = 1.0 if i % 2 == 0 else 0.68 + rng.uniform(-0.05, 0.05)
        pts.append((cx + math.cos(a) * rx * k * 1.12, cy + math.sin(a) * ry * k * 1.25))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon(pts, fill=(*color(spec.get("fill", "#FFFFFF")), 255), outline=(*color(spec.get("outline", "#000000")), 255),
              width=spec.get("width", 8))
    return layer


@lru_cache(maxsize=512)
def render(text, style_name, size, role="main", fill_override=None):
    """Render một cụm chữ (một dòng) theo style. Kết quả được cache."""
    st = load_style(style_name)
    sfx = role == "sfx"
    sr = st.get("sfx_role") or {}
    size = int(size * (sr.get("size_mult", 1.3) if sfx else 1.0))
    fnt = style_font(st["font"], size, st.get("variation"))
    txt = text.upper() if st.get("uppercase") else text
    txt = glyph_safe(txt, fnt)
    fill = color(fill_override or (sr.get("fill") if sfx and sr.get("fill") else st["fill"]))
    stroke = int(st.get("stroke") or 0)
    outline = int(st.get("outline_only") or 0)
    glow = st.get("glow")
    if sfx and sr.get("glow_color") and glow:
        glow = {**glow, "color": sr["glow_color"]}
    shadow = st.get("shadow")
    asc, desc = fnt.getmetrics()
    burst = sr.get("burst") if sfx else None
    pad = 40 + stroke + outline + (int(glow["radius"] * 2) if glow else 0) + \
        (max(abs(v) for v in shadow["offset"]) if shadow else 0) + (burst.get("pad", 40) + 30 if burst else 0)
    total_w = int(fnt.getlength(txt)) + 2 * pad
    total_h = asc + desc + 2 * pad
    letters = []
    colors = st.get("letter_colors")
    jitter = float(st.get("letter_jitter_deg") or 0)
    edge = st.get("paper_edge")
    for i, ch in enumerate(txt):
        if ch.isspace():
            continue
        x = pad + fnt.getlength(txt[:i])
        cw = int(fnt.getlength(ch)) + 2 * (stroke + outline + 14)
        lw, lh = cw + 2 * pad // 2, total_h
        im = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ox = pad // 2 + stroke + outline + 14
        col = color(colors[i % len(colors)]) if colors else fill
        if outline:  # ống neon: chỉ nét viền
            m = Image.new("L", (lw, lh), 0)
            ImageDraw.Draw(m).text((ox, pad), ch, font=fnt, fill=255)
            ring = _outline(np.asarray(m), outline)
            core = cv2.erode(ring, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
            rgb = np.zeros((lh, lw, 3), np.uint8)
            rgb[:] = col
            rgb[core > 0] = (255, 255, 255)  # lõi ống sáng trắng
            im = Image.fromarray(np.dstack([rgb, ring]), "RGBA")
        else:
            if edge:
                d.text((ox, pad), ch, font=fnt, fill=(*color(edge["color"]), 255), stroke_width=edge["width"],
                       stroke_fill=(*color(edge["color"]), 255))
            d.text((ox, pad), ch, font=fnt, fill=(*col, 255), stroke_width=stroke,
                   stroke_fill=(*color(st.get("stroke_color") or "#000000"), 255))
            if st.get("texture"):
                arr = np.asarray(im).copy()
                arr[..., 3] = _texture(arr[..., 3], st["texture"], seed(text, style_name, i))
                im = Image.fromarray(arr, "RGBA")
        if jitter:
            ang = float(_rng(text, style_name, i).uniform(-jitter, jitter))
            im = im.rotate(ang, resample=Image.BICUBIC, expand=False)
        letters.append((im, int(x - ox), 0))
    # ghép
    base = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    for im, x, y in letters:
        base.alpha_composite(im, (max(0, x), y))
    a = np.asarray(base)[..., 3]
    ys, xs = np.nonzero(a > 40)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else (0, 0, 1, 1)
    art = Art(img=base, letters=letters, box=box, fill=fill, style=style_name, role=role, text=text, size=size,
              glow=glow)
    art.img = decorate(base, art)
    return art


def decorate(base, art):
    """Gạch chân, khung nổ, bóng đổ, glow, độ nghiêng của chữ tượng thanh — dùng lại khi ghép chữ theo từng ký tự."""
    st = load_style(art.style)
    sr = st.get("sfx_role") or {}
    sfx = art.role == "sfx"
    w, h = base.size
    base = base.copy()
    if st.get("underline"):
        d = ImageDraw.Draw(base)
        y = art.box[3] + 10
        d.line([(art.box[0], y), (art.box[2], y)], fill=(*art.fill, 255), width=max(3, art.size // 26))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    burst = sr.get("burst") if sfx else None
    if burst:
        out.alpha_composite(_burst((w, h), art.box, burst, seed(art.text)))
    shadow = st.get("shadow")
    if shadow:
        sh = Image.new("RGBA", (w, h), (*color(shadow["color"]), 0))
        sh.putalpha(base.getchannel("A"))
        out.alpha_composite(sh, tuple(int(v) for v in shadow["offset"]))
    glow = art.glow
    if glow:
        g = Image.new("RGBA", (w, h), (*color(glow["color"]), 0))
        g.putalpha(base.getchannel("A").filter(ImageFilter.GaussianBlur(glow["radius"])))
        for _ in range(max(1, int(round(float(glow.get("strength", 1.0)))))):
            out.alpha_composite(g)
    out.alpha_composite(base)
    rot = float(sr.get("rotate", 0)) if sfx else 0.0
    if rot:
        out = out.rotate(rot, resample=Image.BICUBIC, expand=False)
    return out


def fit_size(text, style_name, max_w, role="main", base=None):
    """Cỡ chữ lớn nhất (≤ cỡ của style) để cụm chữ vừa max_w pixel."""
    st = load_style(style_name)
    size = int(base or st["size"])
    mult = (st.get("sfx_role") or {}).get("size_mult", 1.3) if role == "sfx" else 1.0
    txt = text.upper() if st.get("uppercase") else text
    while size > 40:
        f = style_font(st["font"], int(size * mult), st.get("variation"))
        if f.getlength(txt) <= max_w:
            break
        size -= 6
    return size


def boil(rgba, seed, px):
    """Nét chữ rung như frame vẽ tay: dịch chuyển mượt ngẫu nhiên, đổi mỗi `every` frame."""
    if px <= 0:
        return rgba
    arr = np.asarray(rgba)
    h, w = arr.shape[:2]
    rng = np.random.default_rng(seed)
    gx = cv2.resize(rng.uniform(-1, 1, (4, 7)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    gy = cv2.resize(rng.uniform(-1, 1, (4, 7)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    out = cv2.remap(arr, xx + gx * px, yy + gy * px, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return Image.fromarray(out, "RGBA")


def remap(rgba, fx, fy):
    """Biến dạng sprite: fx, fy là hàm(xx, yy) → độ dời (pixel)."""
    arr = np.asarray(rgba)
    h, w = arr.shape[:2]
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    out = cv2.remap(arr, xx + fx(xx, yy), yy + fy(xx, yy), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return Image.fromarray(out, "RGBA")
