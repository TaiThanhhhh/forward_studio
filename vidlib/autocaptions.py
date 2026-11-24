"""Auto-captions word-level karaoke burn-in dùng thẳng mốc từng từ của ElevenLabs.

Preset (`PRESETS`):
  - studio_clean  : thẩm mỹ documentary/explainer người lớn (Vox · Fern · Johnny Harris · Cleo Abram) —
                    Inter-Bold / BeVietnamPro-SemiBold cỡ gọn 48px, chữ thường tự nhiên, nền pill kính mờ tối,
                    từ đang đọc sáng ấm (#F5D547) với micro-pop mượt 1.04×, không viền đen dày kiểu meme
  - capcut_pop    : chữ to đậm viền đen + bóng, từ đang đọc phóng nảy (spring 1.16×) và sáng vàng nổi bật
  - capcut_pill   : từ đang đọc nằm trong viên thuốc (pill) bo tròn màu accent + nảy nhẹ
  - capcut_box    : hộp đen bo tròn gọn kiểu ammedia9192 / CapCut banner, từ đang đọc đổi màu nhấn
  - vox_highlight : dải bút dạ quang vàng Vox (#F5D547) quẹt mượt dưới từ đang đọc
  - off           : tắt burn-in (chỉ xuất file .srt như cũ)

Mặc định đọc từ `config/channel.json → captions` và `layout_grid.captions`, cho phép ghi đè trong
`storyboard.json` (`"captions": "<preset>"`) hoặc cờ CLI `--captions <preset>`.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import lang, textstyle
from .common import ASSETS_DIR, W, channel

PRESETS = ("studio_clean", "capcut_pop", "capcut_pill", "capcut_box", "vox_highlight", "off")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

_SUPPRESS_LAYOUTS = frozenset({"flip", "quote", "kinetic", "left", "center", "stamp", "reveal", ""})
_FONT_CACHE = {}


def _pick_font(candidates, fallback="BeVietnamPro-Black.ttf"):
    for fn in candidates:
        if fn and os.path.exists(os.path.join(FONTS_DIR, fn)):
            return fn
    return fallback


def _load_font(filename, size):
    key = (filename, int(size))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    p = os.path.join(FONTS_DIR, filename)
    if not os.path.exists(p):
        p = os.path.join(FONTS_DIR, _pick_font(("BeVietnamPro-SemiBold.ttf", "BeVietnamPro-Black.ttf")))
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


def should_suppress(shot):
    """True nếu shot đã là thẻ toàn chữ lớn (fact/title) — tự ẩn phụ đề burn-in để không lặp câu 2 lần."""
    if not isinstance(shot, dict):
        return False
    if shot.get("captions") is False:
        return True
    if shot.get("captions") is True:
        return False
    code = shot.get("code") or {}
    if not isinstance(code, dict):
        return False
    scene = str(code.get("scene") or "").strip().lower()
    beat = str(shot.get("beat") or "").strip().lower()
    params = code.get("params") or {}
    layout = str(params.get("layout") or "").strip().lower() if isinstance(params, dict) else ""
    if beat == "twist" and scene == "fact":
        return True
    if scene in ("fact", "title") and layout in _SUPPRESS_LAYOUTS:
        return True
    return False


def resolve_preset(sb=None, override=None, style=None):
    """Chọn preset hoạt động: CLI override > storyboard.captions > style.captions > channel.json."""
    cfg = channel().get("captions") or {}
    default_on = cfg.get("enabled", True)
    default_preset = cfg.get("preset", "studio_clean") if default_on else "off"
    for cand in (override, (sb or {}).get("captions")):
        if cand is False:
            return "off"
        if cand is True:
            return default_preset if default_preset != "off" else "studio_clean"
        if isinstance(cand, str) and cand in PRESETS:
            return cand
    if style:
        st = textstyle.load_style(style)
        sc = st.get("captions")
        if isinstance(sc, str) and sc in PRESETS:
            return sc
    return default_preset if default_preset in PRESETS else "off"


def build_chunks(vo, max_words=3, max_chars=22):
    """Nhóm các từ trong vo['lines'] thành từng cụm 2–4 từ gọn kiểu studio/CapCut, giữ nguyên mốc start/end."""
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


def _ease_out(age_s, dur=0.12):
    """Đường trượt mượt 0 → 1 không overshoot (micro-pop tinh tế cho studio_clean)."""
    if age_s <= 0:
        return 0.0
    if age_s >= dur:
        return 1.0
    t = age_s / dur
    return 1.0 - (1.0 - t) ** 3


class Layer:
    """Lớp vẽ auto-captions từng frame trên ảnh RGB PIL 1080×1920."""

    def __init__(self, vo, preset="studio_clean", style=None):
        self.preset = preset if preset in PRESETS else "off"
        cfg = channel().get("captions") or {}
        def_w = 4 if self.preset in ("studio_clean", "capcut_box") else 3
        def_c = 26 if self.preset == "studio_clean" else (28 if self.preset == "capcut_box" else 22)
        max_w = int(cfg.get("max_words", def_w))
        max_c = int(cfg.get("max_chars", def_c))
        self.chunks = [] if self.preset == "off" else build_chunks(vo, max_words=max_w, max_chars=max_c)
        self.style = style
        self.st = textstyle.load_style(style) if style else {}
        self.upper = self.preset in ("capcut_pop", "capcut_pill")
        self.suppress_on_text_beats = bool(cfg.get("suppress_on_text_beats", True))
        self.smart_nudge = bool(cfg.get("smart_nudge", True))

        # Zone C từ channel.json → layout_grid.captions (mặc định [1340, 1460], tâm cy = 1395)
        grid_cap = (channel().get("layout_grid") or {}).get("captions")
        if isinstance(grid_cap, (list, tuple)) and len(grid_cap) >= 2:
            lo_c, hi_c = int(grid_cap[0]), int(grid_cap[1])
        else:
            lo_c, hi_c = 1340, 1460
        self.zone_c = (max(1330, lo_c - 10), min(1455, hi_c))
        band = (channel().get("safe_zone") or {}).get("caption_band") or [1150, 1450]
        if cfg.get("y") is not None:
            self.cy = int(cfg["y"])
        elif self.preset == "studio_clean":
            self.cy = 1395
        else:
            self.cy = int(band[1] - 40)

        # font & cỡ chữ theo preset
        if cfg.get("font"):
            self.font_file = cfg["font"]
        elif self.preset == "studio_clean":
            cands = (
                ("BeVietnamPro-SemiBold.ttf", "BeVietnamPro-Bold.ttf", "Inter-Bold.otf")
                if lang.language() == "vi"
                else ("Inter-Bold.otf", "BeVietnamPro-SemiBold.ttf", "BeVietnamPro-Bold.ttf")
            )
            self.font_file = _pick_font(cands)
        elif self.preset == "vox_highlight":
            self.font_file = "Caladea-Bold.ttf"
        else:
            self.font_file = "BeVietnamPro-Black.ttf"

        if cfg.get("size"):
            self.base_px = int(cfg["size"])
        elif self.preset == "studio_clean":
            self.base_px = 48
        elif self.preset == "capcut_box":
            self.base_px = 56
        else:
            self.base_px = 68

        # bảng màu theo preset + style
        pal = (self.st.get("html") or {}).get("palette") or self.st.get("palette") or {}
        if self.preset == "studio_clean":
            self.hi_rgb = _hex_rgb(cfg.get("highlight") or "#F5D547", (245, 213, 71))
            self.ink_rgb = (255, 255, 255)
            self.dim_rgb = (200, 205, 214)  # #C8CDD6 (vẽ ở 82% alpha)
        elif self.preset == "vox_highlight":
            self.hi_rgb = (245, 213, 71)
            self.ink_rgb = (246, 243, 236)
            self.dim_rgb = self.ink_rgb
        else:
            self.hi_rgb = _hex_rgb(
                cfg.get("highlight") or (pal.get("c") if self.preset == "capcut_pop" else pal.get("a")) or "#FFE600",
                (255, 230, 0),
            )
            if _luma(self.hi_rgb) < 110 and self.preset == "capcut_pop":
                self.hi_rgb = (255, 230, 0)
            self.ink_rgb = (255, 255, 255)
            self.dim_rgb = self.ink_rgb
        self.pill_rgb = _hex_rgb(cfg.get("pill") or pal.get("a") or "#1849F7", (24, 73, 247))
        self._nudge_cache = {}
        self.last_draw_info = None

    def _active_chunk_with_idx(self, t_abs):
        for idx, ch in enumerate(self.chunks):
            if ch["start"] <= t_abs <= ch["end"]:
                return idx, ch
        return None, None

    def _active_chunk(self, t_abs):
        _, ch = self._active_chunk_with_idx(t_abs)
        return ch

    def _choose_cy(self, img, chunk_idx, shot_id=None):
        """Zone C Smart Vertical Nudge: đo độ sáng + mật độ biên quanh cy vs cy+45 / cy-40 trong [1330, 1455].
        Ổn định theo từng chunk (tránh rung frame-to-frame), chỉ chọn lại khi nền đổi mạnh (cắt cảnh)."""
        lo, hi = self.zone_c
        cy_base = max(lo, min(hi, int(self.cy)))
        if not self.smart_nudge:
            return cy_base, 0.0
        iw, ih = img.size
        if ih < hi + 40 or iw < 200:
            return cy_base, 0.0

        cands = []
        for cand in (cy_base, max(lo, min(hi, cy_base + 45)), max(lo, min(hi, cy_base - 40))):
            if cand not in cands:
                cands.append(cand)

        half_h = 34
        y0 = max(0, min(cands) - half_h)
        y1 = min(ih, max(cands) + half_h)
        x0 = max(0, int(iw * 0.13))
        x1 = min(iw, int(iw * 0.87))
        if y1 - y0 < 8 or x1 - x0 < 16:
            return cy_base, 0.0

        crop_h = y1 - y0
        ds_w = 120
        ds_h = max(12, crop_h // 4)
        gray = np.asarray(
            img.crop((x0, y0, x1, y1)).convert("L").resize((ds_w, ds_h), Image.BILINEAR),
            dtype=np.float32,
        )
        scale_y = ds_h / float(crop_h)

        def score_at(c):
            r0 = max(0, min(ds_h - 2, int(round((c - half_h - y0) * scale_y))))
            r1 = max(r0 + 2, min(ds_h, int(round((c + half_h - y0) * scale_y))))
            band = gray[r0:r1, :]
            luma = float(band.mean())
            gx = float(np.abs(band[:, 1:] - band[:, :-1]).mean()) if band.shape[1] > 1 else 0.0
            gy = float(np.abs(band[1:, :] - band[:-1, :]).mean()) if band.shape[0] > 1 else 0.0
            return 0.55 * luma + 1.8 * (gx + gy)

        key = (chunk_idx, shot_id)
        cached = self._nudge_cache.get(key)
        if cached is not None:
            c_cy, c_score = cached
            cur_score = score_at(c_cy)
            if abs(cur_score - c_score) <= 28.0:
                return c_cy, cur_score

        scores = [(c, score_at(c)) for c in cands]
        base_score = scores[0][1]
        best_cy, best_score = min(scores, key=lambda item: item[1])
        if base_score <= 18.0 or best_score + 10.0 >= base_score:
            chosen_cy, chosen_score = cy_base, base_score
        else:
            chosen_cy, chosen_score = best_cy, best_score
        self._nudge_cache[key] = (chosen_cy, chosen_score)
        return chosen_cy, chosen_score

    def draw(self, img, t_abs, shot=None):
        if self.preset == "off" or not self.chunks:
            self.last_draw_info = None
            return img
        if self.suppress_on_text_beats and should_suppress(shot):
            self.last_draw_info = {"suppressed": True, "preset": self.preset}
            return img
        chunk_idx, ch = self._active_chunk_with_idx(t_abs)
        if not ch:
            self.last_draw_info = None
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

        is_studio = self.preset == "studio_clean"
        if is_studio:
            chunk_pop = 0.985 + 0.015 * _ease_out(age_chunk, 0.10)
            scales = [
                ((1.0 + 0.04 * _ease_out(age_word, 0.12)) if i == active_i else 1.0) * chunk_pop
                for i in range(len(labels))
            ]
        else:
            chunk_pop = 0.90 + 0.10 * _spring(age_chunk, 0.12)
            scales = [
                ((1.0 + 0.14 * _spring(age_word, 0.14)) if i == active_i else 1.0) * chunk_pop
                for i in range(len(labels))
            ]

        # tự co cỡ chữ nếu cụm hơi dài so với chiều rộng an toàn (studio_clean né cột icon phải x=940)
        max_w = 740 if is_studio else W - 180
        min_px = 34 if is_studio else 38
        gap_ratio = 0.30 if is_studio else 0.42
        measure_stroke = 0 if self.preset in ("studio_clean", "capcut_box") else 7
        px = self.base_px
        tmp_d = ImageDraw.Draw(img)
        while px > min_px:
            gap = int(px * gap_ratio)
            ws = [
                tmp_d.textbbox(
                    (0, 0),
                    s,
                    font=_load_font(self.font_file, max(24, int(round(px * scales[i])))),
                    stroke_width=measure_stroke,
                )[2]
                for i, s in enumerate(labels)
            ]
            total_w = sum(ws) + gap * max(0, len(ws) - 1)
            if total_w <= max_w:
                break
            px -= 4

        gap = int(px * gap_ratio)
        fonts = [_load_font(self.font_file, max(24, int(round(px * scales[i])))) for i in range(len(labels))]
        boxes = [tmp_d.textbbox((0, 0), s, font=fonts[i], stroke_width=measure_stroke) for i, s in enumerate(labels)]
        ws = [b[2] - b[0] for b in boxes]
        if is_studio:
            ref_base = tmp_d.textbbox((0, 0), "Hg", font=_load_font(self.font_file, px), stroke_width=0)
            h_line = max(ref_base[3] - ref_base[1], px)
        else:
            h_line = max((b[3] - b[1] for b in boxes), default=px)
        total_w = sum(ws) + gap * max(0, len(ws) - 1)

        shot_id = shot.get("id") if isinstance(shot, dict) else None
        cy, bg_activity = self._choose_cy(img, chunk_idx, shot_id=shot_id)
        iw, ih = img.size
        ov = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        x = (iw - total_w) / 2.0
        pill_box = (int(x), int(cy - h_line / 2), int(x + total_w), int(cy + h_line / 2))

        if is_studio:
            pad_x, pad_y = 26, 14
            bx0 = int(x - pad_x)
            by0 = int(cy - h_line / 2 - pad_y)
            bx1 = int(x + total_w + pad_x)
            by1 = int(cy + h_line / 2 + pad_y)
            pill_box = (bx0, by0, bx1, by1)
            # nền kính mờ tối gọn (0.72 alpha = 184), tự đậm nhẹ nếu nền dưới nhiều chi tiết/sáng
            pill_a = 184 if bg_activity <= 28.0 else min(226, int(184 + (bg_activity - 28.0) * 0.8))
            d.rounded_rectangle([bx0, by0 + 3, bx1, by1 + 3], radius=14, fill=(0, 0, 0, 64))
            d.rounded_rectangle(
                [bx0, by0, bx1, by1],
                radius=14,
                fill=(10, 12, 16, pill_a),
                outline=(255, 255, 255, 23),
                width=1,
            )
        elif self.preset == "capcut_box":
            pad_x, pad_y = 32, 18
            bx0 = int(x - pad_x)
            by0 = int(cy - h_line / 2 - pad_y)
            bx1 = int(x + total_w + pad_x)
            by1 = int(cy + h_line / 2 + pad_y)
            pill_box = (bx0, by0, bx1, by1)
            d.rounded_rectangle([bx0, by0 + 5, bx1, by1 + 5], radius=18, fill=(0, 0, 0, 120))
            d.rounded_rectangle(
                [bx0, by0, bx1, by1],
                radius=18,
                fill=(12, 14, 18, 232),
                outline=(255, 255, 255, 45),
                width=2,
            )

        for i, s in enumerate(labels):
            w_i = ws[i]
            cx_i = x + w_i / 2.0
            is_act = i == active_i
            f_use = fonts[i]
            bb = d.textbbox((0, 0), s, font=f_use, stroke_width=0)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            tx = cx_i - tw / 2.0 - bb[0]
            if is_studio:
                # giữ đúng baseline chữ giữa mọi từ (tránh nhấp nhô giữa từ có/không có ascender/descender)
                ref = d.textbbox((0, 0), "Hg", font=f_use, stroke_width=0)
                ty = cy - (ref[3] - ref[1]) / 2.0 - ref[1]
                fill_col = (*self.hi_rgb, 255) if is_act else (*self.dim_rgb, 209)
                d.text((tx, ty), s, font=f_use, fill=fill_col)
            else:
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
                        d.text(
                            (tx, ty + 5),
                            s,
                            font=f_use,
                            fill=(0, 0, 0, 170),
                            stroke_width=stroke_w + 2,
                            stroke_fill=(0, 0, 0, 170),
                        )
                    d.text((tx, ty), s, font=f_use, fill=fill_col, stroke_width=stroke_w, stroke_fill=(0, 0, 0, 255))
            x += w_i + gap

        self.last_draw_info = {
            "suppressed": False,
            "preset": self.preset,
            "cy": cy,
            "activity": round(bg_activity, 2),
            "box": pill_box,
        }
        return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
