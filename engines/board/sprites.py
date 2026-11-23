"""Dựng sprite cho các vật trên bảng (vẽ một lần lúc build, sau đó chỉ warp).

Mọi kích thước tính bằng đơn vị WORLD; D = số pixel sprite trên một đơn vị world (mặc định 2 → nét vẫn sắc khi
camera đẩy vào ~2×). Màu nhập bằng hex qua `tokens` của style (styles/<style>.json → "board").
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from . import color as col
from . import fonts
from .draw import Sprite

D = 2.0


def _shadowed(body, D, tokens, lift=16, blur=14):
    """Đặt `body` (RGBA) lên nền trong suốt có bóng đổ mềm phía dưới. Trả về (ảnh, pad px)."""
    pad = int((blur * 2.2 + lift) * D)
    w, h = body.size
    c = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = float(tokens.get("shadow", 0.55))
    if a > 0:
        sh = Image.new("L", c.size, 0)
        ImageDraw.Draw(sh).rectangle([pad, pad + lift * D, pad + w, pad + h + lift * D], fill=int(255 * a))
        sh = sh.filter(ImageFilter.GaussianBlur(blur * D))
        c.paste((0, 0, 0, 255), (0, 0), sh)
    c.alpha_composite(body, (pad, pad))
    return c, pad


def _pin(d, x, y, tokens, D):
    r = 9 * D
    d.ellipse([x - r, y - r + 3 * D, x + r, y + r + 3 * D], fill=(0, 0, 0, 110))
    d.ellipse([x - r, y - r, x + r, y + r], fill=col.rgba(tokens.get("pin", "#8a8a86")))
    d.ellipse([x - r * 0.45, y - r * 0.6, x + r * 0.05, y - r * 0.1], fill=(255, 255, 255, 120))


def _tape(img, x, y, w, h, angle, tokens):
    t = Image.new("RGBA", (int(w), int(h)), col.rgba(tokens.get("tape_piece", "#e9e8e2"), 225))
    dd = ImageDraw.Draw(t)
    for k in range(0, int(w), 6):  # mép xé răng cưa
        dd.line([(k, 0), (k + 3, 3)], fill=(0, 0, 0, 0), width=2)
        dd.line([(k, h - 1), (k + 3, h - 4)], fill=(0, 0, 0, 0), width=2)
    t = t.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))


def _clip(d, x, y, tokens, D):
    c = col.rgba(tokens.get("clip", "#b9b9b4"))
    w, h = 26 * D, 78 * D
    d.rounded_rectangle([x, y, x + w, y + h], radius=w / 2, outline=c, width=int(3.2 * D))
    d.rounded_rectangle([x + 6 * D, y + 10 * D, x + w - 6 * D, y + h - 22 * D], radius=w / 3, outline=c, width=int(3 * D))


def _decorate(img, d, x0, y0, w, h, tokens, seed):
    """Ghim / băng dính trắng (chalk) / kẹp giấy (notebook) theo style."""
    deco = tokens.get("deco", "pin")
    rnd = random.Random(seed)
    if deco == "tape":
        _tape(img, x0 + 0.12 * w, y0 + 4 * D, 120 * D, 34 * D, 35 + rnd.uniform(-8, 8), tokens)
        _tape(img, x0 + 0.88 * w, y0 + 4 * D, 120 * D, 34 * D, -35 + rnd.uniform(-8, 8), tokens)
    elif deco == "clip":
        _clip(d, x0 + 0.1 * w, y0 - 26 * D, tokens, D)
    elif deco == "pin":
        _pin(d, x0 + w / 2, y0 + 16 * D, tokens, D)


def media_geom(pw, ph, tokens):
    """(rộng thẻ, cao thẻ, rect ảnh cục bộ quanh tâm thẻ) — dùng chung cho vẽ và cho bộ dàn cảnh (boardplan)."""
    side, bottom = tokens.get("card_border", [16, 64])
    W_, H_ = pw + 2 * side, ph + side + bottom
    return W_, H_, (-W_ / 2 + side, -H_ / 2 + side, -W_ / 2 + side + pw, -H_ / 2 + side + ph)


def media_card(pw, ph, tokens, caption="", seed=0, Dd=D):
    """Thẻ polaroid/màn hình nhỏ chứa clip. Trả về (Sprite, rect ảnh cục bộ (x0, y0, x1, y1) theo world)."""
    side, bottom = tokens.get("card_border", [16, 64])
    W_, H_, _ = media_geom(pw, ph, tokens)
    body = Image.new("RGBA", (int(W_ * Dd), int(H_ * Dd)), col.rgba(tokens.get("card", "#d6d6d0")))
    d = ImageDraw.Draw(body)
    d.rectangle([0, 0, body.width - 1, body.height - 1], outline=col.rgba(tokens.get("card_edge", "#8f8f8a")),
                width=int(1.5 * Dd))
    d.rectangle([side * Dd, side * Dd, (side + pw) * Dd, (side + ph) * Dd], fill=(10, 10, 10, 255))
    if caption:
        sz = min(30, bottom * 0.46)
        tw = fonts.width(caption, "mono", sz * Dd)
        fonts.draw(d, ((W_ * Dd - tw) / 2, (side + ph + (bottom - sz * 1.1) / 2) * Dd), caption, "mono", sz * Dd,
                   col.rgba(tokens.get("ink", "#1b1b1b")))
    img, pad = _shadowed(body, Dd, tokens)
    _decorate(img, ImageDraw.Draw(img), pad, pad, body.width, body.height, tokens, seed)
    anchor = (pad + body.width / 2, pad + body.height / 2)
    return Sprite(col.sprite(img), Dd, anchor), media_geom(pw, ph, tokens)[2]


def tag_size(full, size):
    """(rộng, cao) world của nhãn băng dính — khớp với tag()."""
    padx, pady = 0.45 * size, 0.32 * size
    asc, desc = fonts.metrics("mono", size * D)
    return fonts.width(full + "_", "mono", size * D) / D + 2 * padx, (asc + desc) / D + 2 * pady


def stamp_size(s, size):
    asc, desc = fonts.metrics("serif", size * D)
    return fonts.width(s, "serif", size * D) / D + size * 0.9, (asc + desc) / D + size * 0.55


def paper_layout(lines, w, tokens):
    """Bố cục chữ trên tờ giấy: [(text, role, size, x, y_top, y_baseline, char_boxes)] (toạ độ cục bộ từ góc trái-trên)
    + chiều cao tờ giấy. Dùng chung cho vẽ và cho việc khoanh/gạch đúng một cụm từ."""
    margin = tokens.get("paper_margin", 40)
    y = margin
    out = []
    for ln in lines:
        text, role, size = ln.get("text", ""), ln.get("role", "mono"), float(ln.get("size", 34))
        if not text:
            y += size * 0.8
            continue
        avail = w - 2 * margin
        while fonts.width(text, role, size) > avail and size > 12:
            size *= 0.94
        asc, desc = fonts.metrics(role, size)
        x = margin + (avail - fonts.width(text, role, size)) / 2 if ln.get("align") == "center" else margin
        out.append({"text": text, "role": role, "size": size, "x": x, "top": y, "base": y + asc,
                    "boxes": fonts.char_boxes(text, role, size, x), "h": asc + desc,
                    "color": ln.get("color")})
        y += (asc + desc) * float(ln.get("lead", 1.35))
    return out, y + margin * 0.8


def paper(lines, w, tokens, seed=0, kind="paper", Dd=D):
    """Tờ giấy ghi chép / trang sổ thí nghiệm. `kind`: paper (sáng) | dark (thẻ tối). Trả về (Sprite, layout, (w, h))."""
    lay, h = paper_layout(lines, w, tokens)
    h = max(h, float(tokens.get("paper_min_h", 160)))
    dark = kind == "dark"
    bgc = tokens.get("dark_card" if dark else "paper", "#141414" if dark else "#d8d6ce")
    body = Image.new("RGBA", (int(w * Dd), int(h * Dd)), col.rgba(bgc))
    d = ImageDraw.Draw(body)
    rule = tokens.get("paper_rule")
    if rule and not dark:
        step = tokens.get("paper_rule_step", 30)
        for yy in range(int(step * Dd), body.height, int(step * Dd)):
            d.line([(0, yy), (body.width, yy)], fill=col.rgba(rule), width=max(1, int(Dd)))
    grid = tokens.get("paper_grid")
    if grid and not dark:
        step = int(tokens.get("paper_grid_step", 24) * Dd)
        for xx in range(0, body.width, step):
            d.line([(xx, 0), (xx, body.height)], fill=col.rgba(grid), width=1)
        for yy in range(0, body.height, step):
            d.line([(0, yy), (body.width, yy)], fill=col.rgba(grid), width=1)
    edge = tokens.get("dark_card_edge" if dark else "card_edge", "#5a5a56")
    d.rectangle([0, 0, body.width - 1, body.height - 1], outline=col.rgba(edge), width=int(1.5 * Dd))
    ink = tokens.get("text_light" if dark else "ink", "#ecebe4" if dark else "#1b1b1b")
    for ln in lay:
        fonts.draw(d, (ln["x"] * Dd, ln["top"] * Dd), ln["text"], ln["role"], ln["size"] * Dd, col.rgba(ln["color"] or ink))
    img, pad = _shadowed(body, Dd, tokens)
    _decorate(img, ImageDraw.Draw(img), pad, pad, body.width, body.height, tokens, seed)
    return Sprite(col.sprite(img), Dd, (pad + body.width / 2, pad + body.height / 2)), lay, (w, h)


def card(w, h, tokens, seed=0, rules=None, Dd=D):
    """Thẻ tối trơn (nền cho thẻ số / luận điểm / đồng hồ). rules = [(y_cục_bộ_từ_trên, x0, x1)] vẽ đường kẻ mảnh."""
    body = Image.new("RGBA", (int(w * Dd), int(h * Dd)), col.rgba(tokens.get("dark_card", "#141414")))
    d = ImageDraw.Draw(body)
    d.rectangle([0, 0, body.width - 1, body.height - 1], outline=col.rgba(tokens.get("dark_card_edge", "#5a5a56")),
                width=int(2 * Dd))
    inset = 14 * Dd
    d.rectangle([inset, inset, body.width - 1 - inset, body.height - 1 - inset],
                outline=col.rgba(tokens.get("dark_card_edge", "#5a5a56"), 120), width=max(1, int(Dd)))
    for y, x0, x1 in rules or []:
        d.line([(x0 * Dd, y * Dd), (x1 * Dd, y * Dd)], fill=col.rgba(tokens.get("text_dim", "#9a9993")), width=int(2 * Dd))
    img, pad = _shadowed(body, Dd, tokens)
    _decorate(img, ImageDraw.Draw(img), pad, pad, body.width, body.height, tokens, seed)
    return Sprite(col.sprite(img), Dd, (pad + body.width / 2, pad + body.height / 2))


def text(s, role, size, fill, Dd=D, anchor="center"):
    """Sprite chữ trần (world size `size`). anchor: center | left (neo ở mép trái, giữa dòng)."""
    asc, desc = fonts.metrics(role, size * Dd)
    tw = max(1, int(math.ceil(fonts.width(s, role, size * Dd)))) + 4
    th = int(asc + desc) + 4
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    fonts.draw(ImageDraw.Draw(im), (2, 2), s, role, size * Dd, col.rgba(fill) if isinstance(fill, str) else fill)
    a = (2, th / 2) if anchor == "left" else (tw / 2, th / 2)
    return Sprite(col.sprite(im), Dd, a)


def tag(shown, full, size, tokens, cursor=False, Dd=D):
    """Nhãn băng dính đen, chữ đánh máy. Kích thước băng tính theo chuỗi ĐẦY ĐỦ (băng dán trước, chữ gõ dần).
    Neo ở mép trái-giữa băng."""
    padx, pady = 0.45 * size, 0.32 * size
    tw = fonts.width(full + "_", "mono", size * Dd)
    asc, desc = fonts.metrics("mono", size * Dd)
    w, h = int(tw + 2 * padx * Dd), int(asc + desc + 2 * pady * Dd)
    body = Image.new("RGBA", (w, h), col.rgba(tokens.get("tape", "#0c0c0c")))
    d = ImageDraw.Draw(body)
    d.rectangle([0, 0, w - 1, h - 1], outline=col.rgba(tokens.get("tape_edge", "#3c3c3a")), width=max(1, int(Dd)))
    for k in range(0, h, int(5 * Dd)):  # hai đầu băng xé
        d.line([(0, k), (int(3 * Dd), k + int(2 * Dd))], fill=(0, 0, 0, 0), width=int(2 * Dd))
        d.line([(w - 1, k), (w - 1 - int(3 * Dd), k + int(2 * Dd))], fill=(0, 0, 0, 0), width=int(2 * Dd))
    s = shown + ("_" if cursor else "")
    fonts.draw(d, (padx * Dd, pady * Dd), s, "mono", size * Dd, col.rgba(tokens.get("tape_text", "#ecebe4")))
    img, pad = _shadowed(body, Dd, tokens, lift=4, blur=5)
    return Sprite(col.sprite(img), Dd, (pad, pad + h / 2)), (w / Dd, h / Dd)


def stamp(s, size, tokens, seed=0, Dd=D):
    """Con dấu đỏ: viền đôi + chữ serif, mực loang lổ (mặt nạ nhiễu cố định theo seed)."""
    import numpy as np  # noqa: PLC0415
    red = tokens.get("accent", "#d0312d")
    asc, desc = fonts.metrics("serif", size * Dd)
    tw = fonts.width(s, "serif", size * Dd)
    w, h = int(tw + size * 0.9 * Dd), int(asc + desc + size * 0.55 * Dd)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    b = int(size * 0.075 * Dd)
    d.rectangle([b, b, w - 1 - b, h - 1 - b], outline=col.rgba(red, 240), width=int(size * 0.07 * Dd))
    d.rectangle([b * 3.2, b * 3.2, w - 1 - b * 3.2, h - 1 - b * 3.2], outline=col.rgba(red, 200),
                width=max(1, int(Dd * 1.5)))
    fonts.draw(d, ((w - tw) / 2, (h - asc - desc) / 2), s, "serif", size * Dd, col.rgba(red, 240))
    a = np.array(im)
    rng = np.random.default_rng(seed)
    noise = rng.random(a.shape[:2])
    blot = np.asarray(Image.fromarray((rng.random((max(1, h // 18), max(1, w // 18))) * 255).astype(np.uint8))
                      .resize((w, h), Image.BICUBIC), np.float32) / 255
    keep = (noise > 0.1) & (blot > 0.12)  # mực loang nhẹ: vẫn đọc được (OCR) mà vẫn ra chất con dấu
    a[..., 3] = (a[..., 3] * keep).astype(np.uint8)
    return Sprite(col.sprite(Image.fromarray(a)), Dd)


def image_card(path, w, tokens, seed=0, Dd=D, gray=False):
    """Ảnh tĩnh (ảnh public domain người dùng đưa vào assets/user/, frame phim câm…) trong khung giấy viền xám."""
    im = Image.open(path).convert("RGB")
    if gray:
        im = im.convert("L").convert("RGB")
    side, bottom = tokens.get("card_border", [16, 64])
    pw = w - 2 * side
    ph = pw * im.height / im.width
    body = Image.new("RGBA", (int(w * Dd), int((ph + side + bottom) * Dd)), col.rgba(tokens.get("card", "#d6d6d0")))
    body.paste(im.resize((int(pw * Dd), int(ph * Dd)), Image.LANCZOS), (int(side * Dd), int(side * Dd)))
    img, pad = _shadowed(body, Dd, tokens)
    _decorate(img, ImageDraw.Draw(img), pad, pad, body.width, body.height, tokens, seed)
    return Sprite(col.sprite(img), Dd, (pad + body.width / 2, pad + body.height / 2)), (w, ph + side + bottom)
