"""Font của engine board: mono (máy chữ) + serif đậm (+ chữ tay cho công thức), có dự phòng TỪNG KÝ TỰ.

  mono  = FreeMono Bold   (GNU FreeFont, GPL + font exception — assets/fonts/LICENSE-freefont.txt)
  serif = Caladea Bold    (Apache 2.0 — assets/fonts/LICENSE-caladea.txt)
  hand  = Patrick Hand    (OFL — công thức/ghi chú viết tay)
Ký tự font chính không có (vd →, ≈ ở một số bản) được vẽ bằng font kế tiếp trong chuỗi → không bao giờ ra ô vuông.
`missing(text, role)` liệt kê ký tự KHÔNG font nào trong chuỗi có (QA + test).
"""
import os
from functools import lru_cache, cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
CHAINS = {
    "mono": ["FreeMonoBold.ttf", "FreeSerifBold.ttf"],
    "serif": ["Caladea-Bold.ttf", "FreeSerifBold.ttf", "FreeMonoBold.ttf"],
    "hand": ["PatrickHand-Regular.ttf", "FreeSerifBold.ttf", "FreeMonoBold.ttf"],
}


def chain(role):
    names = CHAINS.get(role) or CHAINS["mono"]
    return [n for n in names if os.path.exists(os.path.join(FONT_DIR, n))]


@lru_cache(maxsize=256)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), max(4, int(round(size))))


@cache
def _notdef(name):
    return _ink(name, "\U000f0000")


@cache
def _ink(name, ch):
    f = font(name, 64)
    im = Image.new("L", (160, 160), 0)
    ImageDraw.Draw(im).text((30, 30), ch, font=f, fill=255)
    return np.asarray(im).tobytes()


@cache
def has(name, ch):
    if ch.isspace():
        return True
    a = _ink(name, ch)
    return any(a) and a != _notdef(name)


def font_for(role, ch):
    names = chain(role)
    for n in names:
        if has(n, ch):
            return n
    return names[0] if names else None


def missing(text, role):
    """Ký tự không font nào trong chuỗi `role` vẽ được (sẽ thành ô vuông)."""
    return sorted({ch for ch in text or "" if not ch.isspace() and not any(has(n, ch) for n in chain(role))})


def runs(text, role):
    """Tách chuỗi thành các đoạn liên tiếp cùng font: [(font_name, đoạn)]."""
    out = []
    for ch in text or "":
        n = font_for(role, ch)
        if out and (out[-1][0] == n or ch.isspace()):
            out[-1] = (out[-1][0], out[-1][1] + ch)
        else:
            out.append((n, ch))
    return out


def width(text, role, size):
    return sum(font(n, size).getlength(s) for n, s in runs(text, role))


def metrics(role, size):
    """(ascent, descent) của font chính."""
    names = chain(role)
    return font(names[0], size).getmetrics() if names else (size, size // 4)


def draw(d, xy, text, role, size, fill):
    """Vẽ chữ có dự phòng từng ký tự lên ImageDraw `d`. xy = góc trên-trái theo baseline của font chính."""
    x, y = xy
    asc, _ = metrics(role, size)
    for n, s in runs(text, role):
        f = font(n, size)
        a2, _ = f.getmetrics()
        d.text((x, y + asc - a2), s, font=f, fill=fill)
        x += f.getlength(s)
    return x


def char_boxes(text, role, size, x0=0.0):
    """[(x_trái, x_phải)] của từng ký tự — để khoanh/gạch đúng một cụm từ."""
    out, x = [], x0
    for ch in text or "":
        w = font(font_for(role, ch), size).getlength(ch)
        out.append((x, x + w))
        x += w
    return out
