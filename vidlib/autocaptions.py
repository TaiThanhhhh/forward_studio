"""Auto-captions kiểu CapCut (word-level karaoke burn-in dùng thẳng mốc từng từ của ElevenLabs).

Preset (`PRESETS`):
  - capcut_pop    : chữ to đậm viền đen + bóng, từ đang đọc phóng nảy (spring 1.16×) và sáng vàng nổi bật
  - capcut_pill   : từ đang đọc nằm trong viên thuốc (pill) bo tròn màu accent + nảy nhẹ
  - capcut_box    : hộp đen bo tròn gọn kiểu ammedia9192 / CapCut banner, từ đang đọc đổi màu nhấn
  - vox_highlight : dải bút dạ quang vàng Vox (#F5D547) quẹt mượt dưới từ đang đọc
  - off           : tắt burn-in (chỉ xuất file .srt như cũ)

Mặc định đọc từ `config/channel.json → captions`, cho phép ghi đè trong `storyboard.json` (`"captions": "<preset>"`)
hoặc cờ CLI `--captions <preset>`.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

from . import textstyle
from .common import ASSETS_DIR, H, W, channel

PRESETS = ("capcut_pop", "capcut_pill", "capcut_box", "vox_highlight", "off")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

_FONT_CACHE = {}


def _load_font(filename, size):
    key = (filename, int(size))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    p = os.path.join(FONTS_DIR, filename)
    if not os.path.exists(p):
        p = os.path.join(FONTS_DIR, "BeVietnamPro-Black.ttf")
    f = ImageFont.truetype(p, int(size))
    _FONT_CACHE[key] = f
    return f


def _hex_rgb(h, fallback=(255, 230, 0)):
    s = str(h or "").strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return fallback
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return fallback


def _luma(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def resolve_preset(sb=None, override=None, style=None):
    """Chọn preset hoạt động: CLI override > storyboard.captions > style.captions > channel.json."""
    cfg = channel().get("captions") or {}
    default_on = cfg.get("enabled", True)
    default_preset = cfg.get("preset", "capcut_pop") if default_on else "off"
    for cand in (override, (sb or {}).get("captions")):
        if cand is False:
            return "off"
        if cand is True:
            return default_preset if default_preset != "off" else "capcut_pop"
        if isinstance(cand, str) and cand in PRESETS:
            return cand
    if style:
        st = textstyle.load_style(style)
        sc = st.get("captions")
        if isinstance(sc, str) and sc in PRESETS:
            return sc
    return default_preset if default_preset in PRESETS else "off"


def build_chunks(vo, max_words=3, max_chars=22):
    """Nhóm các từ trong vo['lines'] thành từng cụm 2–4 từ gọn kiểu CapCut, giữ nguyên mốc start/end của từng từ."""
    if not vo or not vo.get("lines"):
        return []
    chunks = []
    for ln in vo["lines"]:
        words = [w for w in (ln.get("words") or []) if str(w.get("w") or "").strip()]
        cur = []
        for w in words:
            txt = " ".join(x["w"] for x in cur + [w])
            if cur and (len(cur) >= max_words or len(txt) > max_chars):
                chunks.append(cur)
                cur = []
            cur.append({"w": str(w["w"]).strip(), "start": float(w["start"]), "end": float(w["end"])})
            if cur[-1]["w"].endswith((".", "!", "?", ",", ";", ":")) and len(cur) >= 2:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        t0 = c[0]["start"]
        nxt_t0 = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else c[-1]["end"] + 0.35
        t1 = min(c[-1]["end"] + 0.18, max(c[-1]["end"], nxt_t0 - 0.02))
        out.append({"start": t0, "end": t1, "words": c})
    return out


def _spring(age_s, dur=0.14):
    """Đường nảy ngắn 0 → 1 có overshoot nhẹ (~1.16) cho từ vừa bật lên."""
    if age_s <= 0:
        return 0.0
    if age_s >= dur:
        return 1.0
    t = age_s / dur
    return 1.0 - math.exp(-7.0 * t) * math.cos(8.5 * t)


class Layer:
    """Lớp vẽ auto-captions từng frame trên ảnh RGB PIL 1080×1920."""

    def __init__(self, vo, preset="capcut_pop", style=None):
        self.preset = preset if preset in PRESETS else "off"
        cfg = channel().get("captions") or {}
        max_w = int(cfg.get("max_words", 4 if self.preset == "capcut_box" else 3))
        max_c = int(cfg.get("max_chars", 28 if self.preset == "capcut_box" else 22))
        self.chunks = [] if self.preset == "off" else build_chunks(vo, max_words=max_w, max_chars=max_c)
        self.style = style
        self.st = textstyle.load_style(style) if style else {}
        self.upper = self.preset in ("capcut_pop", "capcut_pill")
        # vị trí Y trong caption_band của channel.json (mặc định ~1410 — nằm trên UI đáy TikTok/Shorts)
        band = (channel().get("safe_zone") or {}).get("caption_band") or [1150, 1450]
        self.cy = int(cfg.get("y") or int(band[1] - 40))
        self.font_file = cfg.get("font") or (
            "Caladea-Bold.ttf" if self.preset == "vox_highlight" else "BeVietnamPro-Black.ttf"
        )
        self.base_px = int(cfg.get("size") or (56 if self.preset == "capcut_box" else 68))
        # bảng màu theo preset + style
        pal = (self.st.get("html") or {}).get("palette") or self.st.get("palette") or {}
        self.hi_rgb = (245, 213, 71) if self.preset == "vox_highlight" else _hex_rgb(
            cfg.get("highlight") or (pal.get("c") if self.preset == "capcut_pop" else pal.get("a")) or "#FFE600",
            (255, 230, 0),
        )
        if _luma(self.hi_rgb) < 110 and self.preset == "capcut_pop":
            self.hi_rgb = (255, 230, 0)
        self.pill_rgb = _hex_rgb(cfg.get("pill") or pal.get("a") or "#1849F7", (24, 73, 247))
        self.ink_rgb = (246, 243, 236) if self.preset == "vox_highlight" else (255, 255, 255)

    def _active_chunk(self, t_abs):
        for ch in self.chunks:
            if ch["start"] <= t_abs <= ch["end"]:
                return ch
        return None

    def draw(self, img, t_abs):
        if self.preset == "off" or not self.chunks:
            return img
        ch = self._active_chunk(t_abs)
        if not ch:
            return img
        words = ch["words"]
        labels = [w["w"].upper() if self.upper else w["w"] for w in words]
        # xác định từ đang đọc (giữ từ gần nhất đã bắt đầu)
        active_i = 0
        for i, w in enumerate(words):
            if t_abs >= w["start"] - 0.02:
                active_i = i
        age_chunk = max(0.0, t_abs - ch["start"])
        age_word = max(0.0, t_abs - words[active_i]["start"])
        chunk_pop = 0.90 + 0.10 * _spring(age_chunk, 0.12)

        # tính hệ số scale từng từ trước để căn khoảng cách động — từ phóng to không bao giờ dính sát từ kế bên
        scales = [
            ((1.0 + 0.14 * _spring(age_word, 0.14)) if i == active_i else 1.0) * chunk_pop
            for i in range(len(labels))
        ]
        # tự co cỡ chữ nếu cụm hơi dài so với chiều rộng an toàn (860px)
        max_w = W - 180
        px = self.base_px
        tmp_d = ImageDraw.Draw(img)
        while px > 38:
            gap = int(px * 0.42)
            ws = [
                tmp_d.textbbox((0, 0), s, font=_load_font(self.font_file, max(24, int(round(px * scales[i])))),
                               stroke_width=7)[2]
                for i, s in enumerate(labels)
            ]
            total_w = sum(ws) + gap * max(0, len(ws) - 1)
            if total_w <= max_w:
                break
            px -= 4

        gap = int(px * 0.42)
        fonts = [_load_font(self.font_file, max(24, int(round(px * scales[i])))) for i in range(len(labels))]
        boxes = [tmp_d.textbbox((0, 0), s, font=fonts[i], stroke_width=7) for i, s in enumerate(labels)]
        ws = [b[2] - b[0] for b in boxes]
        h_line = max((b[3] - b[1] for b in boxes), default=px)
        total_w = sum(ws) + gap * max(0, len(ws) - 1)

        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        cy = self.cy
        x = (W - total_w) / 2.0

        # nền hộp chung cho capcut_box (kiểu ammedia9192 / CapCut banner)
        if self.preset == "capcut_box":
            pad_x, pad_y = 32, 18
            bx0 = int(x - pad_x)
            by0 = int(cy - h_line / 2 - pad_y)
            bx1 = int(x + total_w + pad_x)
            by1 = int(cy + h_line / 2 + pad_y)
            d.rounded_rectangle([bx0, by0 + 5, bx1, by1 + 5], radius=18, fill=(0, 0, 0, 120))
            d.rounded_rectangle([bx0, by0, bx1, by1], radius=18, fill=(12, 14, 18, 232),
                                outline=(255, 255, 255, 45), width=2)

        for i, s in enumerate(labels):
            w_i = ws[i]
            cx_i = x + w_i / 2.0
            is_act = i == active_i
            f_use = fonts[i]
            bb = d.textbbox((0, 0), s, font=f_use, stroke_width=0)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            tx = cx_i - tw / 2.0 - bb[0]
            ty = cy - th / 2.0 - bb[1]

            if self.preset == "capcut_pill" and is_act:
                px0 = int(cx_i - tw / 2.0 - 18)
                py0 = int(cy - th / 2.0 - 12)
                px1 = int(cx_i + tw / 2.0 + 18)
                py1 = int(cy + th / 2.0 + 14)
                d.rounded_rectangle([px0, py0 + 4, px1, py1 + 4], radius=16, fill=(0, 0, 0, 130))
                d.rounded_rectangle([px0, py0, px1, py1], radius=16, fill=(*self.pill_rgb, 245))
                fill_col = (14, 16, 20, 255) if _luma(self.pill_rgb) > 165 else (255, 255, 255, 255)
                d.text((tx, ty), s, font=f_use, fill=fill_col)
            elif self.preset == "vox_highlight" and is_act:
                # bút dạ quang vàng quẹt ngang từ trái sang phải theo tiến độ đọc từ
                wdur = max(0.12, words[i]["end"] - words[i]["start"])
                prog = min(1.0, max(0.15, (t_abs - words[i]["start"]) / (wdur * 0.75)))
                hx0 = int(cx_i - tw / 2.0 - 12)
                hx1 = int(hx0 + (tw + 24) * prog)
                hy0 = int(cy - th / 2.0 - 8)
                hy1 = int(cy + th / 2.0 + 12)
                d.rounded_rectangle([hx0, hy0, max(hx0 + 8, hx1), hy1], radius=6, fill=(*self.hi_rgb, 240))
                d.text((tx, ty), s, font=f_use, fill=(14, 16, 20, 255))
            else:
                stroke_w = 0 if self.preset == "capcut_box" else 7
                fill_col = (*self.hi_rgb, 255) if is_act else (*self.ink_rgb, 255)
                if stroke_w:
                    # bóng mềm đáy để nổi trên cả nền sáng 3D lẫn nền tối
                    d.text((tx, ty + 5), s, font=f_use, fill=(0, 0, 0, 170), stroke_width=stroke_w + 2,
                           stroke_fill=(0, 0, 0, 170))
                d.text((tx, ty), s, font=f_use, fill=fill_col, stroke_width=stroke_w, stroke_fill=(0, 0, 0, 255))
            x += w_i + gap

        return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
