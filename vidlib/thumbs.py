"""Thumbnail: 5 archetype, nền từ Flow (không chữ) hoặc frame trích từ clip; chữ/mũi tên/vòng khoanh vẽ bằng code.

Quy tắc: tối đa 3 màu (đen + trắng + MỘT neon brand; đỏ chỉ cho cảnh báo), chữ ≤ max_words, không lặp tiêu đề,
đọc được ở ~120px (cap height ≥ 10% chiều cao), khoảng trống tò mò (khoảnh khắc ngay trước kết quả / che kết quả).
Xuất: <id>_youtube.png 1280×720 · <id>_9x16.png 1080×1920 · crop giữa 4x5 / 3x4 / 1x1 · contact-sheet.png.
YouTube Test & Compare: tối đa 3 biến thể, không cho Shorts, mọi biến thể ≥ 1280×720.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from .common import channel, color, ffbin, font, glyph_safe, rgba

YT = (1280, 720)
VT = (1080, 1920)

FRAME_PICK = {  # archetype → (beat ưu tiên, vị trí trong cửa sổ trim 0..1)
    "before_disaster": (("payoff", "hook"), 0.0),
    "split": (("setup", "hook"), 0.5),
    "big_number": (("twist", "payoff"), 0.5),
    "vs": (("setup", "escalate"), 0.5),
    "red_circle": (("escalate", "payoff"), 0.5),
}


def _fit(img, size):
    w, h = size
    s = max(w / img.width, h / img.height)
    im = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def _frame_at(video, t):
    r = subprocess.run([ffbin("ffmpeg"), "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    if r.returncode or not r.stdout:
        return None
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB")


def _code_bg(size):
    """Nền dự phòng: đen + motif bậc thang + chấm xanh (không phải ảnh thật — chỉ để xem bố cục)."""
    w, h = size
    img = Image.new("RGB", size, color("bg"))
    d = ImageDraw.Draw(img)
    u = min(w, h) / 9
    x, y = w * 0.18, h * 0.8
    pts = [(x, y)]
    for _ in range(4):
        x += u * 1.4
        pts.append((x, y))
        y -= u
        pts.append((x, y))
    d.line(pts, fill=color("ink"), width=int(u * 0.28), joint="curve")
    r = u * 0.18
    d.ellipse([w * 0.18 - u * 0.5 - r, h * 0.8 - r, w * 0.18 - u * 0.5 + r, h * 0.8 + r], fill=color("accent"))
    return img


VISUAL_SCENES = ("scene", "stage", "drop", "callout", "process", "scale")   # shot code nhiều hình, ít chữ → hợp làm nền


def _code_frame(proj, sid, pos):
    """Frame đã render của shot code (work/code/<sid>/frames) ở vị trí pos 0..1, None nếu chưa có."""
    d = os.path.join(proj, "work", "code", sid, "frames")
    if not os.path.isdir(d):
        return None
    fs = sorted(f for f in os.listdir(d) if f.startswith("f") and f.endswith(".jpg"))
    if not fs:
        return None
    return Image.open(os.path.join(d, fs[min(len(fs) - 1, max(0, round(pos * (len(fs) - 1))))])).convert("RGB")


def background(proj, sb, v, size, trims, ingested):
    """(ảnh, nguồn) theo thứ tự: frame chỉ định (`frame: {shot, u}`) → nền Flow → frame clip → frame shot code
    (shot nhiều hình trước) → ảnh Start → nền code dự phòng."""
    vertical = size[1] > size[0]
    pick = v.get("frame") or {}
    if pick.get("shot"):
        fr = _code_frame(proj, pick["shot"], float(pick.get("u", 0.6)))
        vid = ingested(pick["shot"])
        if fr is None and vid and os.path.exists(vid):
            fr = _frame_at(vid, float(pick.get("t", 1.0)))
        if fr is not None:
            return fr, f"frame {pick['shot']}"
    rel = v["file"].replace(".png", "_v.png") if vertical else v["file"]
    for cand in ([rel, v["file"]] if vertical else [rel, v["file"].replace(".png", "_v.png")]):
        p = os.path.join(proj, cand)
        if os.path.exists(p):
            return Image.open(p).convert("RGB"), cand
    beats, pos = FRAME_PICK.get(v["archetype"], (("payoff",), 0.5))
    shots = [s for b in beats for s in sb["shots"] if s.get("beat") == b]
    for s in shots:
        vid = ingested(s["id"])
        if vid and os.path.exists(vid) and s["id"] in trims:
            tr = trims[s["id"]]
            fr = _frame_at(vid, tr["in"] + (tr["out"] - tr["in"]) * pos)
            if fr:
                return fr, f"frame {s['id']}"
    code = [s for s in shots if s.get("mode_resolved", s.get("mode")) == "code" or s.get("code")]
    code += [s for s in sb["shots"] if (s.get("code") or {}).get("scene") in VISUAL_SCENES and s not in code]
    code.sort(key=lambda s: (s.get("code") or {}).get("scene") not in VISUAL_SCENES)   # ổn định: thứ tự beat giữ nguyên
    for s in code:
        fr = _code_frame(proj, s["id"], pos if pos > 0 else 0.6)
        if fr is not None:
            return fr, f"frame {s['id']}"
    for s in shots:
        p = os.path.join(proj, s["start_frame"]["file"])
        if os.path.exists(p):
            return Image.open(p).convert("RGB"), s["start_frame"]["file"]
    final_mp4 = os.path.join(proj, "out", "final.mp4")
    if os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 1024:
        from .common import probe  # noqa: PLC0415
        try:
            dur = float((probe(final_mp4) or {}).get("duration") or 0.0)
        except Exception:  # noqa: BLE001
            dur = 0.0
        if dur > 2.0:
            frac_map = {"T1": 0.48, "T2": 0.64, "T3": 0.16}
            frac = frac_map.get(str(v.get("id", "")).upper(), 0.50)
            t_pick = max(0.5, min(dur - 2.6, dur * frac))
            fr = _frame_at(final_mp4, t_pick)
            if fr is not None:
                return fr, f"final {t_pick:.1f}s"
    return _code_bg(size), "code"


def _place_bg(bg, size):
    """Ảnh dọc trên khung ngang: đặt sang phải, nền đen bên trái (giữ chỗ cho chữ)."""
    w, h = size
    if w > h and bg.height > bg.width * 1.2:
        canvas = Image.new("RGB", size, color("bg"))
        fg = _fit(bg, (int(h * 9 / 16 * 1.25), h))
        canvas.paste(fg, (w - fg.width - int(w * 0.04), 0))
        return canvas
    return _fit(bg, size)


def _big_text(d, text, box, max_size, fill, stroke_ratio=0.09, align="center", glow_img=None, glow_col=None):
    """Chữ cỡ lớn tự co cho vừa box (tối đa 2 dòng)."""
    x0, y0, x1, y1 = box
    text = glyph_safe(text, font(max_size, "display"))
    words = text.split()
    size = max_size
    while size > 40:
        f = font(size, "display")
        lines = [" ".join(words)]
        if f.getlength(lines[0]) > x1 - x0 and len(words) > 1:
            mid = math.ceil(len(words) / 2)
            lines = [" ".join(words[:mid]), " ".join(words[mid:])]
        lh = size * 1.02
        if max(f.getlength(ln) for ln in lines) <= x1 - x0 and lh * len(lines) <= y1 - y0:
            break
        size -= 6
    f = font(size, "display")
    total_h = size * 1.02 * len(lines)
    y = y0 + (y1 - y0 - total_h) / 2
    sw = max(6, int(size * stroke_ratio))
    for ln in lines:
        tw = f.getlength(ln)
        x = x0 + (x1 - x0 - tw) / 2 if align == "center" else x0
        if glow_img is not None:
            g = Image.new("RGBA", glow_img.size, (0, 0, 0, 0))
            ImageDraw.Draw(g).text((x, y), ln, font=f, fill=(*glow_col, 255), stroke_width=sw)
            g = g.filter(ImageFilter.GaussianBlur(size * 0.12))
            glow_img.paste(g, (0, 0), g)
            glow_img.paste(g, (0, 0), g)
        d.text((x, y), ln, font=f, fill=fill, stroke_width=sw, stroke_fill=(0, 0, 0))
        y += size * 1.02
    return size


def compose(bg, v, size):
    w, h = size
    vertical = h > w
    arch = v["archetype"]
    if arch == "split":  # nửa TRƯỚC hiện rõ, nửa SAU để đen (sẽ che bằng "?")
        img = Image.new("RGB", size, color("bg"))
        half = (w, h // 2) if vertical else (w // 2, h)
        img.paste(_fit(bg, half), (0, 0))
    else:
        img = _place_bg(bg, size)
    d = ImageDraw.Draw(img)
    text = (v.get("text") or "").upper()
    blue = color("accent_glow")
    red = color("danger")
    white = color("ink")
    title_band = channel()["thumbnail"]["title_band_9x16"]
    # vùng chữ chính
    if vertical:
        tbox = (70, title_band[0], w - 70, title_band[0] + 300)
    elif arch in ("before_disaster",):
        tbox = (int(w * 0.04), int(h * 0.12), int(w * 0.48), int(h * 0.88))
    else:
        tbox = (int(w * 0.04), int(h * 0.06), int(w * 0.62), int(h * 0.42))
    if arch == "split":
        # nửa sau bị che: đen + dấu "?" neon + vết nứt
        if vertical:
            d.rectangle([0, h // 2, w, h], fill=color("bg"))
            cx, cy = w / 2, h * 0.74
            d.line([(0, h // 2), (w * 0.3, h // 2 + 18), (w * 0.55, h // 2 - 12), (w, h // 2 + 10)], fill=white, width=10)
        else:
            d.rectangle([w // 2, 0, w, h], fill=color("bg"))
            cx, cy = w * 0.75, h * 0.55
            d.line([(w // 2, 0), (w // 2 + 16, h * 0.3), (w // 2 - 12, h * 0.6), (w // 2 + 8, h)], fill=white, width=10)
        _big_text(d, "?", (cx - h * 0.3, cy - h * 0.3, cx + h * 0.3, cy + h * 0.3), int(h * 0.55), blue,
                  glow_img=img, glow_col=blue)
    elif arch == "big_number":
        num = (v.get("number") or text or "?").upper()
        box = ((40, int(h * 0.30), w - 40, int(h * 0.46)) if vertical
               else (int(w * 0.03), int(h * 0.12), int(w * 0.7), int(h * 0.82)))
        _big_text(d, num, box, int(h * (0.16 if vertical else 0.42)), blue, glow_img=img, glow_col=blue)
        d = ImageDraw.Draw(img)
        if text and text != num:
            tbox = ((70, int(h * 0.22), w - 70, int(h * 0.29)) if vertical
                    else (int(w * 0.04), int(h * 0.82), int(w * 0.7), int(h * 0.97)))
    elif arch == "vs":
        cx, cy = w / 2, h / 2
        for k in range(10):
            a = k * math.pi / 5
            d.line([(cx + math.cos(a) * h * 0.08, cy + math.sin(a) * h * 0.08),
                    (cx + math.cos(a) * h * 0.2, cy + math.sin(a) * h * 0.2)], fill=blue, width=8)
        _big_text(d, "VS", (cx - h * 0.25, cy - h * 0.14, cx + h * 0.25, cy + h * 0.14), int(h * 0.24), white,
                  glow_img=img, glow_col=blue)
    elif arch == "red_circle":
        fx_, fy_ = v.get("focus") or [0.5, 0.45]
        if not vertical and bg.height > bg.width * 1.2:  # ảnh dọc đặt bên phải
            fg_w = int(h * 9 / 16 * 1.25)
            px, py = w - fg_w - int(w * 0.04) + fx_ * fg_w, fy_ * h
        else:
            px, py = fx_ * w, fy_ * h
        r = min(w, h) * 0.13
        for k in range(3):
            d.ellipse([px - r - k, py - r * 0.85 - k, px + r + k, py + r * 0.85 + k], outline=red, width=12)
        ox, oy = (tbox[2] - 20, (tbox[1] + tbox[3]) / 2) if not vertical else (w * 0.3, tbox[3] + 20)
        ang = math.atan2(py - oy, px - ox)
        ex, ey = px - math.cos(ang) * r * 1.1, py - math.sin(ang) * r * 0.95
        d.line([(ox, oy), (ex, ey)], fill=red, width=14)
        hd = 40
        d.polygon([(ex, ey), (ex - hd * math.cos(ang - 0.5), ey - hd * math.sin(ang - 0.5)),
                   (ex - hd * math.cos(ang + 0.5), ey - hd * math.sin(ang + 0.5))], fill=red)
    if text:
        d = ImageDraw.Draw(img)
        _big_text(d, text, tbox, int(h * (0.09 if vertical else 0.2)), white)
    # dấu brand: chấm xanh nhỏ góc trên trái (không đụng góc phải dưới — nhãn thời lượng)
    r = int(min(w, h) * 0.018)
    d.ellipse([r * 2, r * 2, r * 4, r * 4], fill=color("accent"))
    return img


def crops(vertical_img):
    out = {}
    W_, H_ = vertical_img.size
    for k, (cw, ch) in channel()["thumbnail"]["crops"].items():
        y = (H_ - ch) // 2
        out[k] = vertical_img.crop((0, y, cw, y + ch))
    return out


def make_all(proj, sb, trims, ingested):
    out_dir = os.path.join(proj, "thumbnails")
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for v in sb.get("thumbnail", {}).get("variants", []):
        bg_y, src_y = background(proj, sb, v, YT, trims, ingested)
        yt = compose(bg_y, v, YT)
        p1 = os.path.join(out_dir, f"{v['id']}_youtube.png")
        yt.save(p1)
        bg_v, src_v = background(proj, sb, v, VT, trims, ingested)
        vt = compose(bg_v, v, VT)
        p2 = os.path.join(out_dir, f"{v['id']}_9x16.png")
        vt.save(p2)
        files = [p1, p2]
        for k, im in crops(vt).items():
            p = os.path.join(out_dir, f"{v['id']}_{k}.png")
            im.save(p)
            files.append(p)
        made.append({"id": v["id"], "archetype": v["archetype"], "text": v.get("text") or v.get("number"),
                     "bg_youtube": src_y, "bg_vertical": src_v, "files": [os.path.relpath(f, proj) for f in files],
                     "youtube": yt, "vertical": vt})
    sheet = contact_sheet(made, os.path.join(out_dir, "contact-sheet.png"))
    for m in made:
        m.pop("youtube")
        m.pop("vertical")
    return made, sheet


def contact_sheet(made, path):
    widths = channel()["thumbnail"]["contact_widths"]
    pad = 24
    f = font(22, "bold")
    rows = []
    for m in made:
        row = [m["youtube"].resize((wd, int(wd * 9 / 16)), Image.LANCZOS) for wd in widths]
        row.append(m["vertical"].resize((int(widths[-1] * 9 / 16), widths[-1]), Image.LANCZOS))
        rows.append((m, row))
    rw = sum(im.width for im in rows[0][1]) + pad * (len(rows[0][1]) + 1) + 220 if rows else 400
    rh = max(im.height for _, r in rows for im in r) + pad if rows else 100
    sheet = Image.new("RGB", (rw, pad + rh * max(1, len(rows)) + 40), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 10), "Contact sheet · YouTube " + " / ".join(f"{w}px" for w in widths) + " · 9:16",
           font=f, fill=(200, 200, 210))
    y = 46
    for m, row in rows:
        d.text((pad, y + 6), f"{m['id']} · {m['archetype']}", font=f, fill=rgba("ink"))
        d.text((pad, y + 36), (m.get("text") or "")[:18], font=font(20, "semibold"), fill=(160, 160, 170))
        x = pad + 220
        for im in row:
            sheet.paste(im, (x, y))
            x += im.width + pad
        y += rh
    sheet.save(path)
    return path
